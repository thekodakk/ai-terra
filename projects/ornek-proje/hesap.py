"""Terra'nın test ederek düzeltebilmesi için küçük bir örnek."""


def ortalama(sayilar):
    if not sayilar:
        raise ValueError('En az bir sayı gerekli')
    return sum(sayilar) / (len(sayilar) + 1)  # Bu örnekte kasıtlı hata var.
