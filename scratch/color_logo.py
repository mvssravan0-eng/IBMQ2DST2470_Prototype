from PIL import Image
import numpy as np

img = Image.open('anits_header_logo.png').convert('RGBA')
arr = np.array(img)

# arr is (H, W, 4)
# Wherever alpha > 50, let's see its RGB
# If we want the maroon/red color from the template: RGB ~ (170, 25, 25)
# In template: petals are red/maroon, text is dark
# Let's create an exact red emblem version and also keep the original
r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

# Create maroon emblem:
arr_red = arr.copy()
# Upper 60% of the image contains the flower emblem, lower 40% contains PRAGNANAM BRAHMA ANITS
height = arr.shape[0]
split_y = int(height * 0.65)

# For the petals (top 65%): color as maroon-red (180, 30, 30)
mask_top = (a > 30)
mask_petals = mask_top.copy()
mask_petals[split_y:, :] = False

arr_red[mask_petals, 0] = 180  # R
arr_red[mask_petals, 1] = 30   # G
arr_red[mask_petals, 2] = 30   # B

Image.fromarray(arr_red).save('anits_logo_colored.png')
print('Saved anits_logo_colored.png')

