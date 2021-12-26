from .colours import Colour
from qrcode.image import styledpil, styles


styles = {
            "drawers": {
                "1": styles.moduledrawers.SquareModuleDrawer(),
                "2": styles.moduledrawers.GappedSquareModuleDrawer(),
                "3": styles.moduledrawers.CircleModuleDrawer(),
                "4": styles.moduledrawers.RoundedModuleDrawer(),
                "5": styles.moduledrawers.VerticalBarsDrawer(),
                "6": styles.moduledrawers.HorizontalBarsDrawer(),
            },
            "masks": {
                "1": styles.colormasks.SolidFillColorMask(),
                "2": styles.colormasks.RadialGradiantColorMask(),
                "3": styles.colormasks.SquareGradiantColorMask(),
                "4": styles.colormasks.HorizontalGradiantColorMask(),
                "5": styles.colormasks.VerticalGradiantColorMask(),
            },
            "colours": {
                "random": lambda: Colour.random(),
                "black": lambda: Colour.black(),
                "white": lambda: Colour.white(),
                "red": lambda: Colour.red(),
                "green": lambda: Colour.green(),
                "blue": lambda: Colour.blue(),
                "yellow": lambda: Colour.yellow(),
                "cyan": lambda: Colour.cyan(),
                "magenta": lambda: Colour.magenta(),
                "grey": lambda: Colour.grey(),
                "gray": lambda: Colour.gray(),
                "orange": lambda: Colour.orange(),
                "purple": lambda: Colour.purple(),
                "brown": lambda: Colour.brown(),
                "pink": lambda: Colour.pink(),
                "lime": lambda: Colour.lime(),
                "olive": lambda: Colour.olive()
            }
        }

