class DtoBase:
    @classmethod
    def from_dict(cls, _dict: dict):
        init_params = {}
        for k in _dict:
            for bcls in cls.__mro__:
                pnmap = getattr(bcls, 'PARAM_NAMES_MAP', {})
                if k in pnmap:
                    init_params[pnmap[k]] = _dict[k]
                    break
                elif bcls is cls.__mro__[-1]:
                    init_params[k] = _dict[k]

        return cls(**init_params)
