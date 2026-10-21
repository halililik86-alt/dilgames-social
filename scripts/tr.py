"""Türkçe yardımcıları."""


def soru_eki(word):
    """Ünlü uyumuna göre soru eki: mağaza → mı, pansiyon → mu, spiker → mi, köprü → mü."""
    for ch in reversed(word.lower()):
        if ch in 'aı': return 'mı'
        if ch in 'ei': return 'mi'
        if ch in 'ou': return 'mu'
        if ch in 'öü': return 'mü'
    return 'mi'
