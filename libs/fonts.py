from __future__ import annotations


class FontResolver:
    FONT_ALIASES: dict[str, list[str]] = {
        "方正小标宋简体": ["FZXiaoBiaoSong-B05S", "方正小标宋简体"],
        "仿宋_GB2312": [
            "FangSong_GB2312",
            "仿宋_GB2312",
            "方正仿宋_GBK",
            "FangSong",
            "仿宋",
            "fangsong",
            "FangSong_GB2312",
        ],
        "黑体": ["SimHei", "黑体", "simhei"],
        "楷体_GB2312": [
            "KaiTi_GB2312",
            "楷体_GB2312",
            "方正楷体_GBK",
            "KaiTi",
            "楷体",
            "kaiti",
            "KaiTi_GB2312",
        ],
        "宋体": ["SimSun", "宋体", "NSimSun", "simsun"],
    }

    REVERSE_ALIASES: dict[str, str] = {}
    for canonical, aliases in FONT_ALIASES.items():
        for alias in aliases:
            REVERSE_ALIASES[alias.lower()] = canonical

    @classmethod
    def resolve(cls, font_name: str) -> str:
        for aliases in cls.FONT_ALIASES.values():
            if font_name in aliases:
                return aliases[0]
        return font_name

    @classmethod
    def normalize(cls, raw_name: str) -> str:
        if not raw_name:
            return ""
        canonical = cls.REVERSE_ALIASES.get(raw_name.lower())
        if canonical:
            return canonical
        for canonical, aliases in cls.FONT_ALIASES.items():
            if raw_name in aliases:
                return canonical
        return raw_name
