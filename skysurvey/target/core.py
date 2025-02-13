import warnings
import numpy as np
import pandas
import inspect
from astropy import cosmology
from astropy.utils.decorators import classproperty

__all__ = ["Target", "Transient"]

from ..template import Template


class Target( object ):

    _KIND = "unknow"
    _TEMPLATE = None
    _MODEL = None # dict config 
    
    # - Cosmo
    _COSMOLOGY = cosmology.Planck18

    def __init__(self):
        """ 
        See also
        --------
        from_setting: loads an instance given model parameters (dict)
        """
        
        
    def __repr__(self):
        """ """
        
        return self.__str__()
    
    def __str__(self):
        """ """
        import pprint
        return pprint.pformat(self.model.model, sort_dicts=False)

    
    @classmethod
    def from_setting(cls, setting, **kwargs):
        """ loads the target from a setting dictionary
        
        = Not Implemented Yet = 

        Parameters
        ----------
        setting: dict
            dictionary containing the model parameters

        **kwargs ....


        Returns
        -------
        class instance
            not implemented yet
        """
        raise NotImplementedError("from_setting is not Implemented ")


    @classmethod
    def from_draw(cls, size=None, model=None, template=None,
                      zmax=None, tstart=None, tstop=None,
                      nyears=None,
                      **kwargs):
        """ loads the instance from a random draw of targets given the model 

        Parameters
        ----------
        size: int, None
            number of target you want to sample
            size=None as in numpy. Usually means 1.
            = ignored if nyears given =

        model: dict, None
            defines how  template parameters to draw and how they are connected
            See "target model documentation"
            = leave to None if unsure, cls._MODEL used as default = 

        template_source: str, None
            name of the template (sncosmo.Model(source)). 
            = leave to None if unsure, cls._TEMPLATE used as default =

        zmax: float
            maximum redshift to be simulated.

        tstart: float
            starting time of the simulation
            
        tstop: float
            ending time of the simulation
            (if tstart and nyears are both given, tstop will be
            overwritten by ``tstart+365.25*nyears``

        nyears: float
            if given, nyears will set:
            - size: it will be the number of target expected up to zmax 
            in the given  number of years. 
            This uses get_rate(zmax).
            - tstop: tstart+365.25*nyears

        **kwargs goes to self.draw()

        Returns
        -------
        class instance
            self.data, self.model and self.template will be loaded.

        See also
        --------
        from_setting:  loads an instance given model parameters (dict)            
        """
        this = cls()
        if model is not None:
            this.set_model(model)

        if template is not None:
            self.set_template(template)
            
        _ = this.draw(size=size, zmax=zmax, tstart=tstart, tstop=tstop,
                      nyears=nyears, **kwargs)
        return this
    
    # ------------- # 
    #   Template    #
    # ------------- #
    def set_template(self, template):
        """ set the template 

        = unlikely you want to set this directly =

        Parameters
        ----------
        template: str, `sncosmo.Source`, `sncosmo.Model` or skysurvey.Template
            This will reset self.template to the new template source.

        See also
        --------
        from_draw: load the instance by a random draw generation.
        from_setting: loads an instance given model parameters
        """
        import sncosmo
        if type(template) is sncosmo.models.Model: # you provided a sncosmo.model.
            template = Template.from_sncosmo_model(template) # let's build a skysurvey.Template
        elif sncosmo.Source in template.__class__.__mro__ or type(template) is str: # you provided a source
            template = Template.from_sncosmo_source(template) # let's build a skysurvey.Template
        else:
            pass # assume it's a template.
            
        self._template = template
        
    def get_template(self, index=None, **kwargs):
        """ get a template (sncosmo.Model) 

        Parameters
        ----------
        index: int, None
            index of a target (see self.data.index) to set the 
            template parameters to that of the target.
            If None, the default sncosmo.Model parameters will be used.
            
        *kwargs goes to seld.template.get() and passed to sncosmo.Model

        Returns
        -------
        sncosmo.Model
            an instance of the template (a sncosmo.Model)

        See also
        --------
        get_target_template: get a template set to the target parameters.
        get_template_parameters: get the template parameters for the given target
        """
        if index is not None:
            prop = self.get_template_parameters(index).to_dict()
            kwargs = {**prop, **kwargs}

        return self.template.get(**kwargs)

    def get_target_template(self, index, **kwargs):
        """ get a template set to the target parameters.

        This is a shortcut to 
        ``get_template(index=index, incl_dust=incl_dust, **kwargs)``

        Parameters
        ----------
        index: int
            index of a target (see self.data.index) to set the 
            template parameters to that of the target.
            
        *kwargs goes to seld.template.get() and passed to sncosmo.Model

        Returns
        -------
        sncosmo.Model
            an instance of the template (a sncosmo.Model)

        See also
        --------
        get_template: get a template instance (sncosmo.Model)
        get_template_parameters: get the template parameters for the given target

        """
        return self.get_template(index=index, **kwargs)

    # -------------- #
    #   Getter       #
    # -------------- #
    def get_template_parameters(self, index=None):
        """ get the template parameters for the given target 
        
        This method selects from self.data the parameters that actually
        are parameters of the template (and disregards the rest).


        Parameters
        ----------
        index: int, None
            index of a target (see self.data.index) to get the 
            template parameters from that target only.

        Returns
        -------
        pandas.DataFrame or pandas.Series
            depending of index

        See also
        --------
        template_parameter: parameters of the template (sncosmo.Model) | argument
        get_template: get a template instance (sncosmo.Model)
        """
        known = self.data.columns[np.in1d(self.data.columns, self.template_parameters)]
        prop = self.data[known]
        if index is not None:
            return prop.loc[index]
        
        return prop

    # -------------- #
    #   Converts     #
    # -------------- #
    def magabs_to_magobs(self, z, magabs, cosmology=None):
        """ converts absolute magnitude into observed magnitude 
        given the (cosmological) redshift and a cosmology 

        Parameters
        ----------
        z: float, array
            cosmological redshift
            
        magabs: float, array
            absolute magnitude

        cosmology: astropy.Cosmology, None
            cosmology to use. If None given, this will use
            the cosmology from self.cosmology (Planck18 by default)

        Returns
        -------
        array
            array of observed magnitude (``distmod(z)+magabs``)
        """
        if cosmology is None:
            cosmology = self.cosmology

        return self._magabs_to_magobs(z, magabs, cosmology=cosmology)
    
    @staticmethod
    def _magabs_to_magobs(z, magabs, cosmology):
        """ converts absolute magnitude into observed magnitude 
        given the (cosmological) redshift and a cosmology 

        = internal method =

        Parameters
        ----------
        z: float, array
            cosmological redshift
            
        magabs: float, array
            absolute magnitude

        cosmology: astropy.Cosmology
            cosmology to use. If None given, this will use
            the cosmology from self.cosmology (Planck18 by default)

        Returns
        -------
        array
            array of observed magnitude (``distmod(z)+magabs``)
        
        """
        return cosmology.distmod(np.asarray(z)).value + magabs

    def draw_radec(cls, model="random", size=None, ra_range=[0,360], dec_range=[-90,90]):
        """ draw the sky positions

        Parameters
        ----------
        model: str
            name of the model. Implemented:
            - random: random homogeneous 2d-sky distribution
            (accounts for dec deformation)

        size: int, None
            number of draw

        ra_range: 2d-array
            right-accension boundaries (min, max)

        dec_range: 2d-array
            declination boundaries
            
        Returns
        -------
        2d-array
            list of ra, list of dec.
        """
        if model == "random":
            dec_sin_range = np.sin(np.asarray(dec_range)*np.pi/180)
            ra = np.random.uniform(*ra_range, size=size)
            dec = np.arcsin( np.random.uniform(*dec_sin_range, size=size) ) / (np.pi/180)
        else:
            raise NotImplementedError("Only the 'random' radec model has been implemented. ")
        
        return ra, dec

    # -------------- #
    #   Model        #
    # -------------- #
    def set_model(self, model):
        """ set the target model 

        what template parameters to draw and how they are connected 

        = It is unlikely you need to use that directly. =

        Parameters
        ----------
        model: dict or ModelDAG,
            model that will be used to draw the Target parameter

        Returns
        -------
        None

        See also
        --------
        from_setting: loads an instance given model parameters (dict)
        from_draw: loads and draw random data.
        """
        from ..dag import ModelDAG
        if type( model ) is dict:
            from copy import deepcopy
            model = ModelDAG(deepcopy(model), self)
            
        
        self._model = model
        
    def get_model(self, **kwargs):
        """ get a copy of the model (dict) 

        You can change the model you get (not the current model)
        using the kwargs. 

        Parameters
        ----------

        **kwargs can change the model entry parameters
            for istance, t0: {"low":0, "high":10}
            will update model["t0"]["param"] = ...

        Returns
        -------
        dict
           a copy of the model (with param potentially updated)
           
           
        See also
        --------
        change_model_parameter: change the current model (not just the one you get)
        get_model_parameter: access the model parameters.
        """
        self.model.get_model(**kwargs)

    def get_model_parameter(self, entry, key, default=None):
        """ access a parameter of the model.

        Parameters
        ----------
        entry: str
            name of the variable as given by the model dict

        key: str
            name of the parameters

        default: 
            value returned if the parameter is not found.

        Returns
        -------
        value of the entry parameter
        
        Example
        -------
        >>> self.get_model_parameter('redshift', 'zmax', None)

        """
        return self.model.model[entry]["param"].get(key, default)

    def change_model_parameter(self, **kwargs):
        """ Change the model parameters

        **kwargs will update any model entry parameters (i.e., the "param", e.g. t0["param"]).

        Example
        -------
        Change the maximum redshift to 1.
        >>> self.change_model_parameter(redshift={"zmax":1})
        """
        _ = self.model.change_model(**kwargs)
        
    # -------------- #
    #   Plotter      #
    # -------------- #
    def show_scatter(self, xkey, ykey, ckey=None, ax=None, fig=None, 
                     index=None, data=None):
        """ """
        import matplotlib.pyplot as plt

        # ------- #
        #  Data   #
        # ------- #
        if data is None:
            data = self.data if index is None else self.data.loc[index]

        xvalue = data[xkey]
        yvalue = data[ykey]
        cvalue = None if ckey is None else data[ckey]

        # ------- #
        #  axis   #
        # ------- #
        if ax is None:
            if fig is None:
                import matplotlib.pyplot as plt
                fig = plt.figure(figsize=[7,4])
            ax = fig.add_subplot(111)
        else:
            fig = ax.figure


        ax.scatter(xvalue, yvalue, c=cvalue)
        return fig
            
    # =============== #
    #   Draw Methods  #
    # =============== #
    def draw(self, size=None,
                 zmax=None, tstart=None, tstop=None,
                 nyears=None,
                 inplace=True, **kwargs):
        """ draws the parameter model (using self.model.draw() 

        Parameters
        ----------
        size: int
            = ignored is nyears is not None =
            number of target you want to draw.

        zmax: float
            maximum redshift to be simulated.

        tstart: float
            starting time of the simulation
            
        tstop: float
            ending time of the simulation
            (if tstart and nyears are both given, tstop will be
            overwritten by ``tstart+365.25*nyears``

        nyears: float
            if given, nyears will set:
            - size: it will be the number of target expected up to zmax 
            in the given  number of years. 
            This uses ``get_rate(zmax)``.
            - tstop: ``tstart+365.25*nyears``

        inplace: bool
            sets self.data to the newly drawn dataframe

        Returns
        -------
        DataFrame
            the simulated dataframe.

        """
        # short cut 
        # -> change the redshift
        if zmax is not None:
            kwargs.setdefault("redshift",{}).update({"zmax": zmax})
            
        elif nyears is not None:
            zmax = self.get_model_parameter("redshift", "zmax", None)
            
        if tstop is not None:
            kwargs.setdefault("t0",{}).update({"high": tstop})
            
        if tstart is not None:
            kwargs.setdefault("t0",{}).update({"low": tstart})
        elif tstop is not None and nyears is not None:
            tstart = tstop - 365.25*nyears # fixed later
        elif nyears is not None:
            tstart = self.get_model_parameter("t0", "low", None)

        if nyears is not None:
            print(zmax)
            kwargs.setdefault("t0",{}).update({"low": tstart, "high": tstart + 365.25*nyears})
            size = int(self.get_rate(zmax) * nyears)

        data = self.model.draw(size=size, **kwargs)
        if inplace:
            self._data = data
            
        return data

    # ============== #
    #   Properties   #
    # ============== #  
    @classproperty
    def kind(self):
        """ """
        if not hasattr(self,"_kind"):
            self._kind = self._KIND
            
        return self._kind
            
    @classproperty
    def cosmology(self):
        """ """
        return self._COSMOLOGY

    # model
    @property
    def model(self):
        """ modeling who the transient is generated """
        if not hasattr(self, "_model") or self._model is None:
            self.set_model(self._MODEL if self._MODEL is not None else {})
            
        return self._model
    
    @property
    def data(self):
        """ data """
        if not hasattr(self,"_data"):
            return None
        return self._data

    # template
    @property
    def template(self):
        """ """
        if not hasattr(self,"_template") or self._template is None:
            self.set_template(self._TEMPLATE)
        return self._template

    @property
    def template_source(self):
        """ """
        return self.template.source

    @property
    def template_parameters(self):
        """ """
        return self.template.parameters
    
    @property
    def template_effect_parameters(self):
        """ """
        return self.template.effect_parameters  


    
class Transient( Target ):
    # - Transient
    _RATE = None    
    
    # ============== #
    #  Methods       #
    # ============== #
    # Rates
    def getpdf_redshift(self, z, **kwargs):
        """ 

        Parameters
        ----------
        z: 1d-array
            list of redshift

        **kwargs goes to get_rate()

        Returns
        -------
        1d-array
            pdf of the redshift distribution
        """
        rates = np.diff(self.get_rate(z, **kwargs))
        return rates/np.nansum(rates)
    
    def get_rate(self, z, **kwargs):
        """ number of target (per year) up to the given redshift

        Parameters
        ----------
        z: float
            redshift

        **wkwargs goes to the rate function (if a function, not a number)

        Returns
        -------
        int
        
        See also
        --------
        getpdf_redshift: the redshift distribution
        rate: float (volumetric_rate) or func (any)
        """
        if callable(self.rate):
            return self.rate(z, **kwargs)
        
        volume = self.cosmology.comoving_volume(z).to("Gpc**3").value
        z_rate = volume * self.rate
        return z_rate
        
    def get_lightcurve(self, band, times,
                           sncosmo_model=None, index=None,
                           in_mag=False, zp=25, zpsys="ab",
                           **kwargs):
        """ the transient lightcurve 

        Parameters
        ----------
        band: str, list
            name of the band (should be known by sncosmo) or list of.

        times: float, list
            time of the observations
            
        Returns
        -------
        nd-array
            1 lightcurve per band.
        """
        # get the template            
        if index is not None:
            prop = self.get_template_parameters(index).to_dict()
            kwargs = {**prop, **kwargs}

        return self.template.get_lightcurve(band, times,
                                            sncosmo_model=sncosmo_model,
                                            in_mag=in_mag, zp=zp, zpsys=zpsys,
                                            **kwargs)

    def get_spectrum(self, time, lbdas, as_phase=True,
                           sncosmo_model=None, index=None,
                           **kwargs):
        """ the transient spectrum at the given phase (time) 

        Parameters
        ----------
        time : float or list_like
            Time(s) in days. If `None` (default), the times corresponding
            to the native phases of the model are used.

        lbdas : float or list_like
            Wavelength(s) in Angstroms. If `None` (default), the native
            wavelengths of the model are used.
            
        as_phase: bool
            Is the given time a phase ? (as_phase=True) or a actual time (False)

        Returns
        -------
        flux : float or `~numpy.ndarray`
            Spectral flux density values in ergs / s / cm^2 / Angstrom.
        
        See also
        --------
        get_lightcurve: get the transient lightcurve 
        """
        # get the template            
        if index is not None:
            prop = self.get_template_parameters(index).to_dict()
            kwargs = {**prop, **kwargs}

        return self.template.get_spectrum(time, lbdas,
                                          sncosmo_model=sncosmo_model,
                                          as_phase=as_phase,
                                          **kwargs)

    # ------------ #
    #  Model       #
    # ------------ #    
    def magobs_to_amplitude(self, magobs, band="bessellb", zpsys="ab", param_name="amplitude"):
        """ """
        template = self.get_template()
        m_current = template._source.peakmag(band,zpsys)
        return 10.**(0.4 * (m_current - magobs)) * template.get(param_name)

    def draw_redshift(self, zmax, zmin=0, zstep=1e-3, size=None):
        """ based on the rate (see get_rate()) """
        xx = np.arange(zmin, zmax, zstep)
        pdf = self.getpdf_redshift(xx)
        return np.random.choice(np.mean([xx[1:],xx[:-1]], axis=0), 
                      size=size, p=pdf/pdf.sum())
            
    # ------------ #
    #  Show LC     #
    # ------------ #
    def show_lightcurve(self, band, index=None, params=None,
                            ax=None, fig=None, colors=None,
                            time_range=[-20,50], npoints=500,
                            zp=25, zpsys="ab",
                            format_time=True, t0_format="mjd", 
                            in_mag=False, invert_mag=True, **kwargs):
        """ 
        params: None or dict
        """
        # get the template
        if params is None:
            params = {}
            
        if index is not None:
            prop = self.get_template_parameters(index).to_dict()
            params = {**prop, **params}

        return self.template.show_lightcurve(band, params=params,
                                             ax=ax, fig=fig, colors=colors,
                                             time_range=time_range, npoints=npoints,
                                             zp=zp, zpsys=zpsys,
                                             format_time=format_time,
                                             t0_format=t0_format, 
                                             in_mag=in_mag, invert_mag=invert_mag,
                                             **kwargs)
            
    # ============== #
    #   Properties   #
    # ============== #  
    # Rate
    @property
    def rate(self):
        """ rate.
        (If float, assumed to be volumetric rate in Gpc-3 / yr-1.)
        """
        if not hasattr(self,"_rate"):
            self._rate = self._RATE # default
            
        return self._rate
