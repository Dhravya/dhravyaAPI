from qrcode.image import styles

_styles = {
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
            }
        }

