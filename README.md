# Logo
This repository contains various representations of my logo, a mix of a `m` and a `1`.
The various versions have been generated from the `m1.svg` file, with different layers displayed or not to achieve the different versions.
In addition to the graphical versions, a font is available as well to import the logo in various programs.

The color palette is <span style="color: #000000"> #0000000 </span> for the pure black and <span style="color:#AA0000"> #AA0000 </span> for the red, with <span style="color: #666666"> #666666 </span> for the greyscale version of the red.

`.png` pictures have been exported for each variant of the logo, in many available resolutions: `16x16`, `32x32`, `48x48`, `64x64`, `128x128`, `256x256`, `512x512`, `1024x1024` and `2048x2048`.


### Clouds
The regular version of the logo, that I use in 99% of cases. The logo has no transparency and features clouds in the background.
This version might be heavy to use as a `.svg` due to the clouds, and using the high-res `.png` version could be better in some cases.

<p align="center">
  <img src="https://github.com/raesangur/logo/blob/master/clouds/m1_clouds_256.png" />
</p>

### Alpha
The regular logo, with an alpha background.

<p align="center">
  <img src="https://github.com/raesangur/logo/blob/master/alpha/m1_alpha_256.png" />
</p>

### White
The regular logo, without transparency and a white background.

<p align="center">
  <img src="https://github.com/raesangur/logo/blob/master/white/m1_white_256.png" />
</p>

### Black and White
A black and white (greyscale) version of the logo, with a white background and no transparency.
This version also has less blur than the previous versions.

<p align="center">
  <img src="https://github.com/raesangur/logo/blob/master/black_white/m1_black_white_256.png" />
</p>

### Outline
A pure outline (in black) of the logo, with a transparent background.

<p align="center">
  <img src="https://github.com/raesangur/logo/blob/master/outline/m1_outline_256.png" />
</p>


# Font
The file `font.ttf` is a TrueType font generated by icomoon.io from the `font.svg` file.
It can be useful to import the black & white, outlined, logo in different programs (notaby CAD software such as Altium Designer) as a font.
As a font, the logo can be scaled easily to any size.

This font contains a single changed character the `m` (`0x6d`) character.
The font is called `m1` on the file system, and I have licensed it under the GNU Public License 3 (GPLv3) like everything else in this repo.

You might need to restart your program for it to refresh its font list after installation.
In certain programs, such as Word, using any other character than `m` will reset the select font to the default document's font.


# Available formats
In addition to the `.png` files, various other formats have also been generated for each variant.

## Vector graphics
`.svg` and `.pdf` pictures have also been exported as vector graphics.
`.pdf` pictures were generated with a 600dpi resolution.
The `.svg` subversions were created from the main `m1.svg`, with unused layers cleaned off, and can be used as vector images directly, to regenerate the `.pdf` files or to generate other formats such as `.html` or `.tex` versions which have not been included in this repository.

## Icons
`.ico` files have been generated for each of the variants. The icons contain a `16x16`, `32x32`, `48x48`, `128x128` and `256x256` version, with 32-bits colors (24 for colors and 8 for transparency), combined into a single `.ico` picture with https://www.icoconverter.com/ 

# ASCII
ASCII Art versions of the logo have been generated using https://www.asciiart.eu/image-to-ascii, with all settings left at default.
Various line width have been generated: 20, 30, 40, 80 and 100.
`@` characters have been used to represent the black `M` part, while `&` characters have been used to represent the red `1` part of the logo.

The echo variants of this ascii art also exist for all dimensions, which print to the console using ANSI colors. These work with any color-supporting ANSI-compliant terminal emulator, which includes the new Windows Terminal and PowerShell. If you wish to use this in the old `cmd.exe` Windows utility, you should set `VirtualTerminalLevel` (`REG_DWORD`) to `1` in the registry under `HKEY_CURRENT_USER\Console`.

# GIF
GIF animations of the logo have been created using Canva, importing the `.svg` into it and playing with its recommended settings in a free trial. The two halves of the logo are in the alpha folder, as `1_alpha.svg` and `m_alpha.svg`.
