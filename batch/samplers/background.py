""""
Copyright 2021 the Norwegian Computing Center

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 3 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
"""

import numpy as np
from utils_unet.np import getGrid, nearest_interpolation


class BackgroundZarr():
    def __init__(self, zarr_files, window_size=(256, 256), check_seabed=None, check_fish=None):
        """
        Sample from zarr-files
        :param zarr_files: (list)
        :param window_size: (tuple), height, width
        """
        self.zarr_files = zarr_files
        self.window_size = window_size
        self.check_seabed = check_seabed
        self.check_fish = check_fish

    def get_sample(self):
        # Select random zarr file in list
        zarr_rand = np.random.choice(self.zarr_files)

        # select random valid ping range in zarr file
        valid_pings_ranges = zarr_rand.get_valid_pings()
        start_ping, end_ping = valid_pings_ranges[np.random.randint(len(valid_pings_ranges))]

        x = np.random.randint(start_ping, end_ping)

        # Get y-loc above seabed
        seabed = int(zarr_rand.get_seabed(x))

        if seabed <= self.window_size[0]//2+1: # If seabed is too shallow
            return self.get_sample()

        y = np.random.randint(self.window_size[0]//2, seabed)

        if self.check_fish:
            # Check if any fish_labels in the crop
            labels = zarr_rand.get_label_slice(idx_ping=x-self.window_size[1]//2,
                                               n_pings=self.window_size[1],
                                               idx_range=max(0, y-self.window_size[0]//2),
                                               n_range=self.window_size[0],
                                               drop_na=False,
                                               return_numpy=False)

            # Check if any fish-labels in crop
            if (labels > 0).any(): # Possible bottleneck?
                return self.get_sample()

        if self.check_seabed is True:
            # Check if there is seabed in the patch, if yes, resample again
            if y + self.window_size[1] // 2 >= seabed:
                y = seabed - (
                            16 + self.window_size[1] // 2)  # Moving the location 10 pixels + half of the window size

        # Check whether the patch is exceeding the echogram
        if y <= self.window_size[1] // 2:
            y = self.window_size[1] // 2
        return [y, x], zarr_rand