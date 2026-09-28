STYLES = {
    'ink': ('mvkit.styles.ink', '水墨江湖'),
    'crayon': ('mvkit.styles.crayon', '蜡笔童画'),
    'paper': ('mvkit.styles.paper', '剪纸月夜'),
}


def load_style(key, P):
    import importlib
    mod = importlib.import_module(STYLES[key][0])
    return mod.Style(P)
