#!/usr/bin/env python3
#coding: utf_8

from loci_objects import Parser
from copy import deepcopy

class gffLine(object):

    def __init__(self,line, my_line='', header=False):
        '''Object which serializes a GFF line.
		Parameters:
				- _line: the original line
				- _fields: the splitted line
				- chrom: the chromosome
				- source: source field, where the data originated from.
				- feature: mRNA, gene, exon, start/stop_codon, etc.
				- start: start of the feature
				- end: stop of the feature
				- strand: strand of the feature
				- score
				- phase
				- attributes - a dictionary which contains the extra information.
				
				Typical fields in attributes are: ID/Parent, Name'''

        self.attributes=dict()
        self.id=None
        self.parent=None
        self.attributeOrder=[]
        if line=='' and my_line=='': return

        if line=='' and my_line!="":
            self._line=my_line
        else:
            self._line=line
        
        self._fields=line.rstrip().split('\t')
        self.header=header
        # if len(self._fields)!=9:
        #     print(*self._line, file=sys.stderr)

        if self.header or len(self._fields)!=9 or self._line=='':
            self.feature=None
            self.header=True
            return

        if len(self._fields)!=9: return None
        self.chrom,self.source,self.feature=self._fields[0:3]
        self.start,self.end=tuple(int(i) for i in self._fields[3:5])

        if self._fields[5]=='.': self.score=None
        else: self.score=float(self._fields[5])

        self.strand=self._fields[6]

        if self._fields[7]=='.': self.phase=None
        else: 
            try: 
                self.phase=int(self._fields[7]); assert self.phase in (0,1,2)
            except: raise

        self._Attr=self._fields[8]

        self.attributeOrder=[]

        for item in [x for x in self._Attr.rstrip().split(';') if x!='']:
            itemized=item.split('=')
            try:
                if itemized[0].lower()=="parent":
                    self.parent=itemized[1]
                elif itemized[1].upper()=="ID":
                    self.id=itemized[1]
                else:
                    self.attributes[itemized[0]]=itemized[1]
                    self.attributeOrder.append(itemized[0])
            except IndexError:
                pass
#                raise IndexError(item, itemized, self._Attr)
            
        if self.id is None:
            id_key = list(filter(lambda x: x.upper()=="ID", self.attributes.keys()))
            if len(id_key)>0:
                id_key=id_key[0]
                self.id = self.attributes[id_key]
        if self.parent is None:
            parent_key = list(filter(lambda x: x.upper()=="PARENT", self.attributes.keys()))
            if len(parent_key)>0:
                parent_key = parent_key[0]
                self.parent = self.attributes[parent_key]

        assert self.parent is not None or self.id is not None, self._line
        _ = self.name # Set the name
            
        if "PARENT" in self.attributes and "Parent" not in self.attributes:
            self.attributes['Parent']=self.attributes['PARENT'][:]
            del self.attributes['PARENT']

    def __str__(self): 
        if not self.feature: return self._line.rstrip()

        if self.score is not None:
            score=str(int(round(self.score,0)))
        else:
            score="."
        if self.strand is None:
            strand='.'
        else:
            strand=self.strand
        if self.phase!=None: phase=str(self.phase)
        else: phase="."
        attrs=[]
        if self.id is not None:
            attrs.append("ID={0}".format(self.id))
        if self.parent is not None:
            attrs.append("Parent={0}".format(",".join(self.parent)))
        if self.attributeOrder==[]:
            self.attributeOrder=sorted(list(filter(lambda x: x not in ["ID","Parent"], self.attributes.keys())))
        for att in filter(lambda x: x not in ["ID","Parent"],  self.attributeOrder):
            if self.attributes[att] is not None:
                try: attrs.append("{0}={1}".format(att, self.attributes[att]))
                except: continue #Hack for those times when we modify the attributes at runtime
            
        line='\t'.join(
            [self.chrom, self.source,
             self.feature, str(self.start), str(self.end),
             str(score), strand, phase,
             ";".join(attrs)]
        )
        return line

    def __len__(self):
        if "end" in self.__dict__:
            return self.end-self.start+1
        else: return 0

    @property
    def id(self):
        return self.attributes["ID"]
    @id.setter
    def id(self,Id):
        self.attributes["ID"]=Id
        
    @property
    def parent(self):
        '''This property looks up the "Parent" field in the "attributes" dictionary. Contrary to other attributes,
        this property returns a *list*, not a string. This is due to the fact that GFF files support
        multiple inheritance by separating the parent entries with a comma.'''
        if "Parent" not in self.attributes:
            self.parent=None
        return self.attributes["Parent"]
    @parent.setter
    def parent(self,parent):
        if parent is None:
            self.attributes["Parent"]=None
        elif type(parent) is str:
            if "," in parent:
                parent=parent.split(",")
            else:
                parent=[parent]        
            self.attributes["Parent"]=parent
        elif type(parent) is list:
            self.attributes["Parent"]=parent
        else:
            raise TypeError(parent, type(parent))
    
    @property
    def name(self):
        if "Name" not in self.attributes:
            self.name=self.id
        return self.attributes["Name"]
    @name.setter
    def name(self,name):
        self.attributes["Name"]=name

    @property
    def strand(self):
        return self.__strand
    
    @strand.setter
    def strand(self,strand):
        if strand in ("+", "-"):
            self.__strand=strand
        elif strand in (None,".","?"):
            self.__strand=None
        else:
            raise ValueError("Invalid value for strand: {0}".format(strand)) 

    @property
    def score(self):
        return self.__score
    
    @score.setter
    def score(self,*args):
        if type(args[0]) in (float,int):
            self.__score=args[0]
        elif args[0] is None or args[0]=='.':
            self.__score = None
        elif type(args[0]) is str:
            self.__score=float(args[0])
        else:
            raise TypeError(args[0])
        
    @property
    def is_exon(self):
        if self.feature in ("CDS","exon") or "utr" in self.feature.lower() :
            return True
        return False
        
    @property
    def is_transcript(self):
        if "transcript"==self.feature or "RNA" in self.feature.upper():
            return True
        return False
        
    @property
    def is_parent(self):
        if self.parent is None:
            return True
        return False
        

class GFF3(Parser):
    def __init__(self,handle):
        super().__init__(handle)
        self.header=False
        
    def __next__(self):
        
        if self.closed:
            raise StopIteration

        line=self._handle.readline()
        if line=='': raise StopIteration

        if line[0]=="#":
            return gffLine(line, header=True)

        line=gffLine(line)
        if line.parent is not None and "," in line.parent:
            print(line.parent.split(","))
            newLines=[]
            for parent in line.parent.split(","):
                newLine=deepcopy(line)
                newLine.parent = parent
                newLines.append(newLine)
            return newLines
        else:
            return line
            
        
