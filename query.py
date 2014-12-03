"""

"""
import subprocess
import configparser

configPath = "config/"

class vizquery:

    def __init__(self, RA=None, DEC=None):
        """
            Initiates the class taking the given RA and DEC and retrieving the
            names of the config files that the class will query.

            Parameters
            ----------
                    RA : string
                    The right-ascension of the object to query, in sexagesimal.

                    DEC : string
                    The declination of the object to query, again in
                    sexagesimal.

            Returns
            -------
                    None
        """
        self.ra = RA
        self.dec = DEC
        self.data = {}
        import os
        self.sources = [f for f in os.listdir(configPath) if (os.path.isfile(os.path.join(configPath, f))) and ('.ini' in f)]

    def __readConfig__(self, source):
        """
            Reads the config file given the name of the file 'source'.

            Parameters
            ----------
                    source : string
                    The name of the config file with the query parameters.

            Returns
            -------
                    None
        """
        self.config = configparser.ConfigParser()
        self.config.read("{}{}".format(configPath, source))

    def __makeQuery__(self, source):
        """
            Takes the parameters for the source in the config file and makes a
            dictionary of the parameters then stores them as an attribute of the
            class.

            Parameters
            ----------
                    source : string
                    The name of the file with the parameters for the query.

            Returns
            -------
                    None
        """
        conf = self.config['query']

        self.queryParams = {
                            'object' : "{} {}".format(self.ra, self.dec),
                            'source' : conf['source'],
                            'radius' : conf['radius'],
                            'output' : conf['output'],
                            'max'    : conf['max']
                            }

    def __runQuery__(self):
        """
            Performs the query of VizieR using the cdsclient and a dictionary of
            parameters.

            Parameters
            ----------
                    None

            Returns
            -------
                    None
        """
        query = "vizquery -source='{source}' -c='{object}' -c.rs='{radius}' -out='{output}' -sort='_r' -out.max='{max}' -mime='csv'".format(**self.queryParams)

        (self.raw, self.err) = subprocess.Popen(query, 
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, 
                                        shell=True).communicate()

        self.raw = self.raw.split('\n')

    def __cleanData__(self):
        """
            Takes the retrieved data and removes lines of crap, forces the
            correct data types and deletes any nan data.

            Parameters
            ----------
                    None

            Returns
            -------
                    None
        """
        conf = self.config['reduce']

        excludes = [f for f in conf['exclude'].split()] + ['#', '---']
        types = [eval(f) for f in conf['types'].split()]

        self.__removeLines__(excludes)
        self.__forceTypes__(types)
        self.__deleteNans__()

    def __removeLines__(self, excludes):
        """
            Removes all the crap VizieR spits out that is not the data.

            Parameters
            ----------
                    excludes : list
                    A list of the strings to compare to the lines to remove
                    them.

            Returns
            -------
                    None
        """
        for i in reversed(range(len(self.raw))):
            for exclude in excludes:
                if (exclude in self.raw[i]):
                    self.raw.pop(i)

        self.raw = self.raw[1].split(';')

    def __forceTypes__(self, types):
        """
            Forces each column of data to be of a certain type depending on the
            types list.

            Parameters
            ----------
                    types : list
                    List of types to force the data to be.

            Returns
            -------
                    None
        """
        for n, item in enumerate(self.raw):
            if types[n] == str:
                self.raw[n] = self.raw[n].strip()
            else:
                try:
                    self.raw[n] = types[n](self.raw[n])
                except ValueError as e:
                    from numpy import nan
                    self.raw[n] = nan

    def __deleteNans__(self):
        """
            Deletes lists of data where all the entries are nans.

            Parameters
            ----------
                    None

            Returns
            -------
                    None
        """
        from numpy import isnan

        if (len(self.raw) == 1) and (isnan(self.raw[0])):
            self.raw = None

        else:
            try:
                if all([isnan(x) for x in self.raw]):
                    self.raw = None
            except TypeError as e:
                pass

    def query(self, notSources=[]):
        """
            Queries VizieR for data using config files for each
            survey/catalogue. End result is an attribute of the class called
            'data' where each source is a key pointing to the list of the raw
            data.

            Parameters
            ----------
                    notSources : list
                    A list of the sources to exclude from the query.

            Returns
            -------
                    None
        """

        for source in self.sources:
            if source not in notSources:
                self.__readConfig__(source)
                self.__makeQuery__(source)
                self.__runQuery__()
                self.__cleanData__()
                self.data[source.replace('.ini', '')] = self.raw

