# coding: utf_8

"""
Generic parser for GTF files.
"""

from . import Parser
from .gfannotation import GFAnnotation
import re


# This class has exactly how many attributes I need it to have
# pylint: disable=too-many-instance-attributes
class GtfLine(GFAnnotation):
    """This class defines a typical GTF line, with some added functionality
    to make it useful in e.g. parsing cufflinks GTF files or
    creating GTF lines from scratch.
    Fields:
    - chrom
    - source
    - feature
    - start,end
    - score
    - phase
    - strand
    - info (a dictionary containing all the annotations contained in the last field)

    - gene: the gene_id
    - transcript: the transcript_id

    For cufflinks files, also:
    - nearest_ref
    - tss_id
    - ccode"""

    # _slots=['chrom','source','feature','start',\
    # 'end','score','strand','phase','info']

    _attribute_pattern = re.compile(r"([^;\s]*) \"([^\"]*)\"(?:;|$)")

    def __init__(self, line, my_line='', header=False):

        self.__frame = None
        self.__phase = None
        GFAnnotation.__init__(self, line, my_line, header=header)
        # self.frame = self.__phase  # Reset the phase

    def _parse_attributes(self):
        """
        Method to retrieve the attributes from the last field
        of the GTF line.
        :return:
        """

        # for info in iter(x for x in self._attr.rstrip().split(';') if x != ''):
        #     info = info.strip().split(' ')
        #     # info_list.append(info)
        #     # info = info.lstrip().split(' ')
        #     try:
        #         self.attributes[info[0]] = info[1].replace('"', '')
        #     except IndexError as exc:
        #         # something wrong has happened, let us just skip
        #         import sys
        #         print("Wrong attributes ({}) in line:\n{}".format(info, "\t".join(self._fields)), file=sys.stderr)
        #     if info[0] == "exon_number":
        #         self.attributes['exon_number'] = int(self.attributes['exon_number'])

        infodict = dict(re.findall(self._attribute_pattern, self._attr.rstrip()))
        for key, val in infodict.items():
            try:
                val = int(val)
            except ValueError:
                try:
                    val = float(val)
                except ValueError:
                    val = val.replace('"', '')
            self.attributes[key] = val

    def _format_attributes(self):

        """
        Private method to format the last field of the GTF line
        prior to printing.
        :return:
        """

        info_list = []
        assert 'gene_id', 'transcript_id' in self.attributes
        if isinstance(self.gene, list):
            gene = ",".join(self.gene)
        else:
            gene = self.gene
        self.attributes['gene_id'] = gene
        order = ['gene_id', 'transcript_id', 'exon_number', 'gene_name', 'transcript_name']

        for tag in order:
            if tag in self.attributes:
                if isinstance(self.attributes[tag], list):
                    val = ",".join(self.attributes[tag])
                else:
                    val = self.attributes[tag]
                info_list.append("{0} \"{1}\"".format(tag, val))

        for info in iter(key for key in self.attributes if
                         self.attributes[key] not in (None, "", []) and key not in order):
            if (info == "Parent" and
                        self.attributes[info] in (self.gene,
                                                  self.transcript,
                                                  self.parent)):
                continue
            if info == "ID" and self.attributes[info] in (self.gene, self.transcript):
                continue

            if isinstance(self.attributes[info], list):
                val = ",".join(self.attributes[info])
            else:
                val = self.attributes[info]
            info_list.append("{0} \"{1}\"".format(info, val))
        attributes = "; ".join(info_list) + ";"
        return attributes

    @property
    def name(self):
        """
        Returns the name of the feature. It defaults to the ID if missing.
        :rtype str
        """
        if "Name" not in self.attributes:
            self.name = self.id
        return self.attributes["Name"]

    @name.setter
    def name(self, *args):
        """
        Setter for name. The argument must be a string.
        :param args:
        :type args: list[(str)] | str
        """

        if not isinstance(args[0], (type(None), str)):
            raise TypeError("Invalid value for name: {0}".format(args[0]))
        self.attributes["Name"] = args[0]

    @property
    def is_transcript(self):
        """
        Flag. True if feature is "transcript" or contains "RNA", False in all other cases.
        :rtype : bool
        """
        if self.feature is None:
            return False
        if "transcript" == self.feature or "RNA" in self.feature:
            return True
        return False

    @property
    def parent(self):
        """This property looks up the "Parent" field in the "attributes" dictionary.
        If the line is a transcript line, it returns the gene field.
        Otherwise, it returns the transcript field.
        In order to maintain interface consistency with
        the GFF objects and contrary to other attributes,
        this property returns a *list*, not a string. This is due
        to the fact that GFF files support
        multiple inheritance by separating the parent entries with a comma.

        :rtype : list

        """

        if self.is_transcript is True:
            return [self.gene]
        else:
            return [self.transcript]

    @parent.setter
    def parent(self, parent):
        """
        Setter for parent. Acceptable values
        :param parent: the new parent value
        :type parent: list | str
        """
        if isinstance(parent, str):
            parent = parent.split(",")
        self.attributes["Parent"] = parent
        if self.is_transcript is True:
            self.gene = parent

    # pylint: disable=invalid-name
    @property
    def id(self):
        """
        ID of the line. "transcript_id" for transcript features, None in all other cases.
        :rtype : str | None
        """
        if self.is_transcript is True:
            return self.transcript
        else:
            return None

    @id.setter
    def id(self, newid):
        """
        Setter for id. Only transcript features can have their ID set.
        :param newid: the new ID
        """
        if self.is_transcript is True:
            self.transcript = newid
        else:
            pass
    # pylint: enable=invalid-name

    @property
    def gene(self):
        """
        Return the "gene_id" field.
        :rtype : str | None
        """

        # if "gene_id" not in self.attributes and self.is_transcript is True:
        #     self.attributes["gene_id"] = self.parent[0]
        return self.attributes["gene_id"]

    @gene.setter
    def gene(self, gene):
        """
        Setter for gene.
        :param gene:
        :rtype : str

        """

        self.attributes["gene_id"] = self.__gene = gene
        if self.is_transcript:
            self.attributes["Parent"] = gene

    @property
    def transcript(self):
        """
        This property returns the "transcript_id" field of the GTF line.
        :rtype : str
        """
        return self.attributes.get("transcript_id", None)

    @transcript.setter
    def transcript(self, transcript):
        """
        Setter for the transcript attribute. It also modifies the "transcript_id" field.
        :param transcript:
        :type transcript: str
        """

        self.attributes["transcript_id"] = self._transcript = transcript
        if self.is_transcript is True:
            self.attributes["ID"] = transcript
        else:
            self.attributes["Parent"] = [transcript]

    @property
    def is_parent(self):
        """
        True if we are looking at a transcript, False otherwise.
        :rtype : bool
        """
        if any([self.is_transcript, self.is_gene]):
            return True
        return False

    @property
    def is_derived(self):
        """
        Property. It checks whether there is a "Derives_from" attribute among the line attributes.
        :rtype bool
        """
        return "derives_from" in iter(x.lower() for x in self.attributes)

    @property
    def derived_from(self):
        """
        Boolean property. True if the GTF line has a "derives_from" tag,
        False otherwise.
        """
        if self.is_derived is False:
            return None
        else:
            key = list(key for key in self.attributes if
                       key.lower == "derives_from")[0]
            return self.attributes[key].split(",")

    @property
    def is_gene(self):
        """
        In a GTF this should always evaluate to False
        """
        return self.feature == "gene"

    @property
    def frame(self):
        """
        Frame of the GTF record line. It can be one of None, 0, 1, 2.
        :return:
        """

        return self.__frame

    @property
    def _negative_order(self):
        return ["3UTR",
                "exon",
                "stop_codon",
                "CDS",
                "start_codon",
                "5UTR"]

    @property
    def _positive_order(self):
        return ["5UTR",
                "exon",
                "start_codon",
                "CDS",
                "stop_codon",
                "3UTR"]

    @property
    def phase(self):
        return self.__phase

    @phase.setter
    def phase(self, value):
        if isinstance(value, str):
            if value.isdigit() is True:
                value = int(value)
                if value not in (0, 1, 2):
                    raise ValueError(value)
                self.__phase = value
                self.__frame = (3 - value) % 3
            else:
                if value not in (".", "?"):
                    raise ValueError(value)
                self.__phase = self.__frame = None
        elif value is None:
            self.__frame = self.__phase = None
        elif isinstance(value, int):
            if value not in (0, 1, 2):
                raise ValueError(value)
            self.__phase = value
            self.__frame = (3 - value) % 3
        else:
            raise ValueError(value)


class GTF(Parser):
    """The parsing class."""

    __annot_type__ = "gtf"

    def __init__(self, handle):
        """
        Constructor for the parser.
        :param handle: either the filename or the handle for the file to parse.
        :return:
        """

        super().__init__(handle)

    def __next__(self):
        line = self._handle.readline()
        if line == '':
            raise StopIteration
        return GtfLine(line)

    @property
    def file_format(self):
        return self.__annot_type__
