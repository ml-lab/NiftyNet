import six
import scipy
import nibabel
import numpy as np
import numpy.ma as ma
import scipy.stats.mstats as mstats
from util import MorphologyOps
from util import SimpleCache

class RegionProperties(object):
    def __init__(self, seg, img, measures,
            num_neighbors=24, threshold=0, pixdim=[1,1,1]):

        self.seg = seg
        self.img = img
        img_id = range(0, img.shape[3] if img.ndim == 4 else 1)
        self.m_dict = {
                'centre of mass': (self.centre_of_mass, ['CoMx',
                                                         'CoMy',
                                                         'CoMz']),
                'volume': (self.volume,
                    ['NVoxels', 'NVoxelsBinary', 'Vol', 'VolBinary']),
                'surface': (self.surface, ['NSurface',
                                           'NSurfaceBinary',
                                           'SurfaceVol',
                                           'SurfaceVolBinary']),
                'surface volume ratio': (self.sav, ['SAVNumb',
                                                    'SAVNumBinary',
                                                    'SAV',
                                                    'SAVBinary']),
                'compactness': (self.compactness, ['CompactNumb',
                                                   'CompactNumbBinary',
                                                   'Compactness',
                                                   'CompactnessBinary']),
                'mean': (self.mean_, ['Mean_%d'%i for i in img_id]),
                'weighted_mean': (self.weighted_mean_,
                                  ['Weighted_mean_%d'%i for i in img_id]),
                'median': (self.median_, ['Median_%d'%i for i in img_id]),
                'skewness': (self.skewness_, ['Skewness_%d'%i for i in img_id]),
                'kurtosis': (self.kurtosis_, ['Kurtosis_%d'%i for i in img_id]),
                'min': (self.min_, ['Min_%d'%i for i in img_id]),
                'max': (self.max_, ['Max_%d'%i for i in img_id]),
                'quantile_25': (self.quantile_25,
                                 ['P25_%d'%(i) for i in img_id]),
                'quantile_50': (self.median_,
                                 ['P50_%d'%(i) for i in img_id]),
                'quantile_75': (self.quantile_75,
                                 ['P75_%d'%(i) for i in img_id]),
                'std': (self.std_, ['STD_%d'%i for i in img_id]),
                }
        self.measures = measures
        self.neigh = num_neighbors
        self.pixdim = pixdim
        self.threshold = threshold
        if self.seg is not None:
            self.masked = self.__compute_mask()
        self.vol_vox = np.prod(pixdim)

    def __compute_mask(self):
        mask_temp = 1 - self.seg
        mask_temp[mask_temp < 0.5] = False
        mask_temp[mask_temp >= 0.5] = True
        mask_temp = np.tile(mask_temp, [1, 1, 1, self.img.shape[3]])
        masked_array = ma.masked_array(self.img, mask_temp)
        return masked_array.reshape(-1, masked_array.shape[-1])

    def centre_of_mass(self):
        return np.mean(np.argwhere(self.seg > self.threshold), 0)

    @SimpleCache
    def volume(self):
        numb_seg = np.sum(self.seg)
        numb_seg_bin = np.sum(self.seg > 0)
        return numb_seg, numb_seg_bin,\
               numb_seg * self.vol_vox, numb_seg_bin * self.vol_vox

    @SimpleCache
    def surface(self):
        border_seg = MorphologyOps(self.seg, self.neigh).border_map()
        numb_border_seg_bin = np.sum(border_seg > 0)
        numb_border_seg = np.sum(border_seg)
        return numb_border_seg, numb_border_seg_bin, \
               numb_border_seg * self.vol_vox, numb_border_seg_bin * self.vol_vox

    def sav(self):
        Sn,Snb,Sv,Svb = self.surface()
        Vn,Vnb,Vv,Vvb = self.volume()
        return Sn/Vn, Snb/Vnb, Sv/Vv, Svb/Vvb

    def compactness(self):
        Sn,Snb,Sv,Svb = self.surface()
        Vn,Vnb,Vv,Vvb = self.volume()
        return np.power(Sn, 1.5) / Vn, np.power(Snb, 1.5) / Vnb, \
                np.power(Sv,1.5) / Vv, np.power(Svb,1.5) / Vvb

    def min_(self):
        return ma.min(self.masked, 0)

    def max_(self):
        return ma.max(self.masked, 0)

    def weighted_mean_(self):
        weights = np.tile(self.seg,
                [1, 1, 1, self.img.shape[3]]).reshape(-1, self.masked.shape[-1])
        return ma.average(self.masked, axis=0, weights=weights).flatten()

    def mean_(self):
        return ma.mean(self.masked, 0)

    def skewness_(self):
        return mstats.skew(self.masked, 0)

    def std_(self):
        return ma.std(self.masked, 0)

    def kurtosis_(self):
        return mstats.kurtosis(self.masked, 0)

    def median_(self):
        return ma.median(self.masked, 0)

    def quantile_25(self):
        return mstats.mquantiles(self.masked, prob=0.25, axis=0).flatten()

    def quantile_75(self):
        return mstats.mquantiles(self.masked, prob=0.75, axis=0).flatten()

    def header_str(self):
        result_str = ""
        for i in self.measures:
            for j in self.m_dict[i][1]:
                result_str += ',' + j
        return result_str

    def to_string(self, fmt='{:4f}'):
        result_str = ""
        for i in self.measures:
            for j in self.m_dict[i][0]():
                try:
                    result_str += ',' + fmt.format(j)
                except ValueError:  #some functions give strings e.g., "--"
                    result_str += ',{}'.format(j)
        return result_str
