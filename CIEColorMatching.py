import numpy as np

class ColorMatchingCIE:
    # source/inspo: https://www.baeldung.com/cs/rgb-color-light-frequency
    def __init__(self):
        self.wavelengths = {}
        self.wavelengths_simple = {}

        for wl in np.arange(350, 750):
            self.wavelengths[wl] = self.get_rgb(wl)   # CIE
            self.wavelengths_simple[wl] = self.get_simple_rgb(wl)   # simplified (not CIE)

    def get_rgb(self, wavelength):
        def get_X(wavelen):
            # X is considered to represent the hue and saturation on the red-green axis.
            if wavelen < 442.0:
                factor1 = 0.0624
            else:
                factor1 = 0.0374

            if wavelen < 599.8:
                factor2 = 0.0264
            else:
                factor2 = 0.0323

            if wavelen < 501.1:
                factor3 = 0.0490
            else:
                factor3 = 0.0382

            Xt1 = (wavelen - 442.0) * factor1
            Xt2 = (wavelen - 599.8) * factor2
            Xt3 = (wavelen - 501.1) * factor3

            return (0.362 * np.exp(-0.5 * (Xt1 ** 2))) + (1.056 * np.exp(-0.5 * (Xt2 ** 2))) - (0.065 * np.exp(-0.5 * (Xt3 ** 2)))

        def get_Y(wavelen):
            # Y is considered to represent the luminosity.
            if wavelen < 568.8:
                factor1 = 0.0213
            else:
                factor1 = 0.0247
            if wavelen < 530.9:
                factor2 = 0.0613
            else:
                factor2 = 0.0322
            Yt1 = (wavelen - 568.8) * factor1
            Yt2 = (wavelen - 530.9) * factor2

            return (0.821 * np.exp(-0.5 * (Yt1 ** 2))) + (0.286 * np.exp(-0.5 * (Yt2 ** 2)))

        def get_Z(wavelen):
            # Z is considered to represent the hue and saturation on the blue-yellow axis.
            if wavelen < 437.0:
                factor1 = 0.0845
            else:
                factor1 = 0.0278
            if wavelen < 459.0:
                factor2 = 0.0385
            else:
                factor2 = 0.0725

            Zt1 = (wavelen - 437.0) * factor1
            Zt2 = (wavelen - 459.0) * factor2

            return (1.217 * np.exp(-0.5 * (Zt1 ** 2))) + (0.681 * np.exp(-0.5 * (Zt2 ** 2)))

        def calc_rgb(X, Y, Z):
            # calculate raw RBG values
            r_factors = [3.2406255, -1.537208, -0.4986286]
            g_factors = [-0.9689307, 1.8757561, 0.0415175]
            b_factors = [0.0557101, -0.2040211, 1.0569959]

            R_raw = r_factors[0]*X + r_factors[1]*Y + r_factors[2]*Z
            G_raw = g_factors[0]*X + g_factors[1]*Y + g_factors[2]*Z
            B_raw = b_factors[0]*X + b_factors[1]*Y + b_factors[2]*Z

            return R_raw, G_raw, B_raw

        def gamma_correction(value):
            # apply gamma correction and convert them to 0-255 range
            if value <= 0:
                return 0
            elif value <= 0.0031308:
                return round(255*value*12.92)
            elif value <= 1:
                return round(255 * (1.055 * (value**(1/2.4)) - 0.055 ))
            else:
                return 255

        X = get_X(wavelength)
        Y = get_Y(wavelength)
        Z = get_Z(wavelength)
        #print(X, Y, Z)
        R_raw, G_raw, B_raw = calc_rgb(X, Y, Z)
        #print(R_raw, G_raw, B_raw)

        R = gamma_correction(R_raw)
        G = gamma_correction(G_raw)
        B = gamma_correction(B_raw)
        #print(R, G, B)
        return '#{:02x}{:02x}{:02x}'.format(R, G, B)
        #return [R, B, G]

    def get_simple_rgb(self, wl):
        if 645 < wl <= 780:
            red = 1
            green = 0
            blue = 0
        elif 580 < wl <= 645:
            red = 1
            green = -(wl-645)/(645-580)  # FIXME -(wl-645)/(645/580)
            blue = 0
        elif 510 < wl <= 580:
            red = (wl-510)/(580-510)
            green = 1
            blue = 0
        elif 490 < wl <= 510:
            red = 0
            green = 1
            blue = -(wl-510)/(510-490)
        elif 440 < wl <= 490:
            red = 0
            green = (wl-440)/(490-440)
            blue = 1
        elif 380 < wl <= 440:
            red = -(wl-440)/(440-380)
            green = 0
            blue = 1
        else:
            red = 0
            green = 0
            blue = 0

        if 700 < wl <= 780:
            factor = 0.3 + (0.7*(780-wl)/(780-700))
        elif 420 < wl <= 700:
            factor = 1
        elif 380 < wl <= 420:
            factor = 0.3 + (0.7*(wl-380)/(420-380))
        else:
            factor = 0

        R = round(255*(red*factor)**0.8)
        G = round(255*(green*factor)**0.8)
        B = round(255*(blue*factor)**0.8)

        return '#{:02x}{:02x}{:02x}'.format(R, G, B)