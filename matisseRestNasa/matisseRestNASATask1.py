# -*- coding:utf-8 -*-
import string
import urllib2
from datetime import datetime
from xml.dom import minidom
from xml.parsers import expat
import argparse



import logging

__REST_NASA__ = 'http://oderest.rsl.wustl.edu/live2/?query=p&output=XML&r=Mf'

test_url='http://oderest.rsl.wustl.edu/live2/?target=moon&query=p&output=XML&ihid=CH1-ORB&iid=M3&pt=CALIV3&r=fm&westernlon=10&easternlon=15&minlat=20&maxlat=25'

"""

usage: matisseRestNASA.py [-h] --target TARGET --ihid IHID --iid IID
                          [--c1min WESTERNLON] [--c1max EASTERNLON]
                          [--c2min MINLAT] [--c2max MAXLAT]
                          [--Time_min MINOBTIME] [--Time_max MAXOBTIME]
                          [--Incidence_min MININANGLE]
                          [--Incidence_max MAXINANGLE]
                          [--Emerge_min MINEMANGLE] [--Emerge_max MAXEMANGLE]
                          [--Phase_min MINPHANGLE] [--Phase_max MAXPJANGLE]
                          [--log LOG]

optional arguments:
  -h, --help            show this help message and exit
  --c1min WESTERNLON    Min of first coordinate (in degrees by default)
  --c1max EASTERNLON    Max of first coordinate (in degrees by default)
  --c2min MINLAT        Min of second coordinate (in degrees by default)
  --c2max MAXLAT        Max of second coordinate (in degrees by default)
  --Time_min MINOBTIME  Acquisition start time - format YYYY-MM-DDTHH:MM:SS.m
  --Time_max MAXOBTIME  Acquisition stop time - format YYYY-MM-DDTHH:MM:SS.m
  --Incidence_min MININANGLE
                        Min incidence angle (solar zenithal angle)
  --Incidence_max MAXINANGLE
                        Max incidence angle (solar zenithal angle)
  --Emerge_min MINEMANGLE
                        Min emerge angle
  --Emerge_max MAXEMANGLE
                        Max emerge angle
  --Phase_min MINPHANGLE
                        Min phase angle
  --Phase_max MAXPJANGLE
                        Max phase angle

  --log LOG             log file, default stdout


required  arguments:
  --target TARGET       PDS target name
  --ihid IHID           instrument host ID
  --iid IID             instrument ID
"""


class NASAQueryException(Exception):
    pass


class NASAQuery(object):

    """ NASAQuery class sets all the parameters needed for the query.
    Ables to perform the query and to return the results

    Mandatory Attributes:
      target (str): target to query
      ihid (str): ID
      iid (str): instrument ID
    """
    def __init__(self, target=None, ihid=None, iid=None, **parameters):

        self.target = target
        self.ihid = ihid
        self.iid = iid
        #not mandatory parameter, this takes parameters dynamical
        for name, value in parameters.iteritems():
            setattr(self, name, value)



    def composeURLMoon(self):
        """
         single URL:
         compose the url with pt hardcoded
         Return: url string 
        """

        parameters = '&'.join(['%s=%s' % (item, value) for item, value in self.__dict__.iteritems()
                               if value])

        return __REST_NASA__ + '&pt=CALIV3&' + parameters

    @staticmethod
    def read_nodelist(nodelist):
        """
        Utility method to read the content of a nodeList
        :rtype : object
        :param nodelist:
        :return: string of the xml element
        """
        if nodelist:
            return " ".join(t.nodeValue for t in nodelist[0].childNodes if t.nodeType == t.TEXT_NODE)
        else:
            return None

    def readMetadata(self, xml_tag):
        """
        Read the metadata of the observation
        :param: xml that contains al the metadata information
        :return: dictionary with all metadata read
        """
        import matisse_configuration as cfg
     
        metadata = {}
        metadata['Observation_time'] = self.read_nodelist(xml_tag.getElementsByTagName('Observation_time'))
        metadata['SpaceCraft_clock_start_count'] = self.read_nodelist(xml_tag.getElementsByTagName('SpaceCraft_clock_start_count'))
        metadata['SpaceCraft_clock_stop_count'] = self.read_nodelist(xml_tag.getElementsByTagName('SpaceCraft_clock_stop_count'))
        metadata['Start_orbit_number'] = self.read_nodelist(xml_tag.getElementsByTagName('Start_orbit_number'))
        metadata['Stop_orbit_number'] = self.read_nodelist(xml_tag.getElementsByTagName('Stop_orbit_number'))
        metadata['UTC_start_time'] = self.read_nodelist(xml_tag.getElementsByTagName('UTC_start_time'))
        metadata['UTC_stop_time'] = self.read_nodelist(xml_tag.getElementsByTagName('UTC_stop_time'))
        metadata['Solar_distance_text'] = self.read_nodelist(xml_tag.getElementsByTagName('Solar_distance_text'))
        metadata['Center_georeferenced'] = self.read_nodelist(xml_tag.getElementsByTagName('Center_georeferenced'))
        metadata['Center_latitude'] = self.read_nodelist(xml_tag.getElementsByTagName('Center_latitude'))
        metadata['Center_longitude'] = self.read_nodelist(xml_tag.getElementsByTagName('Center_longitude'))
        metadata['BB_georeferenced'] = self.read_nodelist(xml_tag.getElementsByTagName('BB_georeferenced'))
        metadata['Easternmost_longitude'] = self.read_nodelist(xml_tag.getElementsByTagName('Easternmost_longitude'))
        metadata['Maximum_latitude'] = self.read_nodelist(xml_tag.getElementsByTagName('Maximum_latitude'))
        metadata['Minimum_latitude'] = self.read_nodelist(xml_tag.getElementsByTagName('Minimum_latitude'))
        metadata['Westernmost_longitude'] = self.read_nodelist(xml_tag.getElementsByTagName('Westernmost_longitude'))

        return metadata

    def fetchData(self, a_url):

        info_files = {}

        xmlNASA = urllib2.urlopen(a_url)
        xmldoc = minidom.parseString(xmlNASA.read())
        #here select all the product tags
        products = xmldoc.getElementsByTagName('Product')
        for a_tag in products:
            files = []
            id_filename = None
            metadata = self.readMetadata(a_tag)
            #loops over the product tag and select for each product the product files
            product_file = a_tag.getElementsByTagName("Product_file")


            for a_file in product_file:
                #loop over the product_file for each product 
                type_tag = a_file.getElementsByTagName('Type')
                #select the type tag Product
                if self.read_nodelist(type_tag) == 'Product':
                    file_name = self.read_nodelist(a_file.getElementsByTagName('FileName'))
                    string_array = file_name.split("_")
                    string_array.pop()
                    id_filename = "_".join(string_array)
                    if file_name.endswith('LOC.IMG') or file_name.endswith('LOC.HDR') or file_name.endswith('RDN.IMG') \
                            or file_name.endswith('RDN.HDR'):
                        files.append(self.read_nodelist(a_file.getElementsByTagName('URL')))

                info_files[id_filename] = {'metadata': metadata, 'files':files}


        return info_files




    def associateFiles(self):

        return  self.fetchData(self.composeURLMoon())





def valid_date(s):
    """"
    Validation of the command line options.
    Check if a date is of the right format
    e.g. = 2013-01-08T15:39:05.169

    Arg: string
    Return: string
    Raise ArgumentTypeError
    """

    try:
        datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f")
        #date string is well formatted
        return s
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def main(parser, id_filename=None, metadata=None, files=None):

    #creates the NASAQuery obj
    nq = NASAQuery()
    # Parse the arguments and directly load in the NASAQuery namespace
    args = parser.parse_args(namespace=nq)

    #setup the logging
    log_format = "%(message)s"
    if args.log:
        logging.basicConfig(filename=args.log, filemode='w',
                            format=log_format, level=logging.INFO)
    else:
        logging.basicConfig(format=log_format, level=logging.INFO)

    #associate the files
    info_files = nq.associateFiles()

    for id_filename in info_files:
        print "This is the File ID : %s" % id_filename
        print "Metadata for the File"
        metadata = info_files[id_filename]['metadata']
        for k,v in metadata.iteritems():
            print "%s: %s" % (k,v)
        print "Associated Files"
        for a_file in info_files[id_filename]['files']:
            print a_file



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="")
  # Define the command line options

    requiredNamed = parser.add_argument_group('required  arguments')
    requiredNamed.add_argument('--target', dest='target',
                        help="PDS target name", required=True)
    requiredNamed.add_argument('--ihid', dest='ihid', help="instrument host ID", required=True)
    requiredNamed.add_argument('--iid', dest='iid', help="instrument  ID", required=True)

    #coordinates (c1, c2, c3)
    parser.add_argument('--c1min', dest='westernlon', type=float,
                        help="Min of first coordinate (in degrees by default)")
    parser.add_argument('--c1max', dest='easternlon', type=float,
                        help="Max of first coordinate (in degrees by default)")
    parser.add_argument('--c2min', type=float, dest='minlat',
                        help="Min of second coordinate (in degrees by default) ")
    parser.add_argument('--c2max', type=float, dest='maxlat',
                        help="Max of second coordinate (in degrees by default) ")

    #times
    parser.add_argument('--Time_min', dest='minobtime', type=valid_date,
                        help="Acquisition start time - format YYYY-MM-DDTHH:MM:SS.m")
    parser.add_argument('--Time_max', dest='maxobtime', type=valid_date,
                        help="Acquisition stop time - format YYYY-MM-DDTHH:MM:SS.m")
    #angles

    parser.add_argument('--Incidence_min', dest='mininangle', type=float,
                        help="Min incidence angle (solar zenithal angle)")

    parser.add_argument('--Incidence_max', dest='maxinangle', type=float,
                        help="Max incidence angle (solar zenithal angle)")

    parser.add_argument('--Emerge_min', dest='minemangle', type=float,
                        help="Min emerge angle")

    parser.add_argument('--Emerge_max', dest='maxemangle', type=float,
                        help="Max emerge angle")

    parser.add_argument('--Phase_min', dest='minphangle', type=float,
                        help="Min phase angle")

    parser.add_argument('--Phase_max', dest='maxpjangle', type=float,
                        help="Max phase angle")

    parser.add_argument('--log', dest='log',
                        help="log file, default stdout")
   

    main(parser)



