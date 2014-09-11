import copy
import metarelate.fuseki as fuseki
import metarelate

umf = '<http://www.metarelate.net/metOcean/format/um>'
cff = '<http://www.metarelate.net/metOcean/format/cf>'
st = '<http://reference.metoffice.gov.uk/um/f3/stash>'
eq = '<http://www.openmath.org/cd/relation1.xhtml#eq>'
cfsn = '<http://def.cfconventions.org/datamodel/standard_name>'
snpref = '<http://def.cfconventions.org/standard_names/'
cfu = '<http://def.cfconventions.org/datamodel/units>'
cffield = '<http://def.cfconventions.org/datamodel/Field>'
cftype = '<http://def.cfconventions.org/datamodel/type>'
nsav = '<http://www.metarelate.net/metOcean/people/nhsavage>'
marqh = '<http://www.metarelate.net/metOcean/people/marqh>'



def parse_batch(fuseki_process, afile='/project/avd/metarelate/sharespace/stashOwners/classic_s0'):
    with open(afile, 'r') as inputs:
        for line in inputs.readlines()[1:]:
            line = line.rstrip('\n')
            lsplit = line.split('|')
            unitsprop = metarelate.Property(None,
                                            ptype="<http://def.cfconventions.org/datamodel/units>",
                                            value='"{}"'.format(lsplit[2]))
                                            # "<http://www.openmath.org/cd/relation1.xhtml#eq>")
            unitsprop.create_rdf(fuseki_process)
            #import pdb; pdb.set_trace()
            name = lsplit[1]
            sns = fuseki_process.subject_and_plabel('http://cf/cf-standard-name-table.ttl')
            snames = [sn['notation'] for sn in sns]
            if name in snames:
                nprop = metarelate.Property(None,
                                             ptype = "<http://def.cfconventions.org/datamodel/standard_name>",
                                             closematch = '"{}"'.format(name))#,
                                             #"<http://www.openmath.org/cd/relation1.xhtml#eq>")
            else:
                nprop = metarelate.Property(None,
                                             ptype = "<http://def.cfconventions.org/datamodel/long_name>",
                                             value = '"{}"'.format(name))#,
                                             #"<http://www.openmath.org/cd/relation1.xhtml#eq>")
            nprop.create_rdf(fuseki_process)
            newtarget = metarelate.PropertyComponent(None, com_type='<http://def.cfconventions.org/datamodel/Field>',
                                                 properties = [unitsprop, nprop])
            newtarget.create_rdf(fuseki_process)
            # import pdb; pdb.set_trace()
            # newtarget = metarelate.Concept(None, cff, newpc)
            # newtarget.create_rdf(fuseki_process)
            stashprop = metarelate.Property(None,
                                            ptype = "moumdpF3:stash",
                                            closematch = 'moStCon:{}'.format(lsplit[0]))#,
                                            #"<http://www.openmath.org/cd/relation1.xhtml#eq>")
            stashprop.create_rdf(fuseki_process)
            newsource = metarelate.PropertyComponent(None, com_type="moumdpF3:stash",
                                                     properties=[stashprop])
            # spc = metarelate.PropertyComponent(None, [stashprop])
            # newsource = metarelate.Concept(None, umf, spc)
            newsource.create_rdf(fuseki_process)
            new_mapping = metarelate.Mapping(None, newsource, newtarget,
                                             editor=marqh, reason='"new mapping"',
                                             status = '"Draft"')
            new_mapping.create_rdf(fuseki_process)
            #import pdb; pdb.set_trace()
            #break

                

with fuseki.FusekiServer() as fuseki_process:
    #fuseki_process.load()
    parse_batch(fuseki_process)
    
