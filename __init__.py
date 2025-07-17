from krita import Krita
from .quick_access_manager import QuickAccessManagerExtension

Krita.instance().addExtension(QuickAccessManagerExtension(Krita.instance()))
