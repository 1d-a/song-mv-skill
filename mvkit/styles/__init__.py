STYLES = {
    'ink': ('mvkit.styles.ink', '水墨江湖'),
    'crayon': ('mvkit.styles.crayon', '蜡笔童画'),
    'paper': ('mvkit.styles.paper', '剪纸月夜'),
}


def out_frame(S, t):
    """style frame cropped to the project's aspect; styles set `view_y`, the top row of the crop"""
    a = S.frame(t)
    return a if S.P.OH == a.shape[0] else a[S.view_y:S.view_y + S.P.OH]


def load_style(key, P):
    import importlib
    mod = importlib.import_module(STYLES[key][0])
    return mod.Style(P)
