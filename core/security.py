from model import PIIMasker

masker = PIIMasker()

def pii_mask(doc):
    return masker.mask_pii(doc)
