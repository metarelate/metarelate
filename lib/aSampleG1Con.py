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


def make_sample(fuseki_process):
    g1param = '<http://reference.metoffice.gov.uk/grib/edition1/localparams/165>'
    fuom = 'm s-1'
    fname = 'x_wind'
    cname = 'height'
    cuom = 'm'
    ch = 10
    unitsprop = metarelate.Property(None,
                                    ptype="<http://def.cfconventions.org/datamodel/units>",
                                    value='"{}"'.format(fuom))
    unitsprop.create_rdf(fuseki_process)
    
    sns = fuseki_process.subject_and_plabel('http://cf/cf-standard-name-table.ttl')
    snames = [sn['notation'] for sn in sns]
    if fname in snames:
        nprop = metarelate.Property(None,
                                     ptype = "<http://def.cfconventions.org/datamodel/standard_name>",
                                     closematch = '"{}"'.format(fname))
    else:
        nprop = metarelate.Property(None,
                                     ptype = "<http://def.cfconventions.org/datamodel/long_name>",
                                     value = '"{}"'.format(fname))
    nprop.create_rdf(fuseki_process)

    if cname in snames:
        cprop = metarelate.Property(None,
                                     ptype = "<http://def.cfconventions.org/datamodel/standard_name>",
                                     closematch = '"{}"'.format(cname))
    else:
        cprop = metarelate.Property(None,
                                     ptype = "<http://def.cfconventions.org/datamodel/long_name>",
                                     value = '"{}"'.format(cname))
    cprop.create_rdf(fuseki_process)
    cunitsprop = metarelate.Property(None,
                                    ptype="<http://def.cfconventions.org/datamodel/units>",
                                    value='"{}"'.format(cuom))
    cunitsprop.create_rdf(fuseki_process)
    chprop = metarelate.Property(None,
                                    ptype="<http://def.cfconventions.org/datamodel/points>",
                                    value='"{}"'.format(ch))
    chprop.create_rdf(fuseki_process)
                                    
    subcomp = metarelate.PropertyComponent(None, com_type='<http://def.cfconventions.org/datamodel/DimensionCoordinate>',
                                           properties = [cunitsprop, cprop,chprop])
    subcomp.create_rdf(fuseki_process)

    newtarget = metarelate.Component(None, com_type='<http://def.cfconventions.org/datamodel/Field>',
                                     properties = [unitsprop, nprop],
                                     components = [subcomp])
    newtarget.create_rdf(fuseki_process)
    gprop = metarelate.Property(None,
                                    ptype = "<http://codes.wmo.int/def/gribcore/message>",
                                    closematch = g1param)
    gprop.create_rdf(fuseki_process)
    newsource = metarelate.PropertyComponent(None, com_type="moumdpF3:stash",
                                             properties=[gprop])
    newsource.create_rdf(fuseki_process)
    new_mapping = metarelate.Mapping(None, newsource, newtarget,
                                     editor=marqh, reason='"new mapping"',
                                     status = '"Draft"')
    new_mapping.create_rdf(fuseki_process)
                

with fuseki.FusekiServer() as fuseki_process:
    #fuseki_process.load()
    make_sample(fuseki_process)
    import pdb; pdb.set_trace()
    
