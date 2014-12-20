import cPickle, os, re


def get_disease_specific_drugs(drug_to_diseases, phenotype_to_mesh_id):
    disease_to_drugs = {}
    mesh_id_to_phenotype = {}
    for phenotype, mesh_id in phenotype_to_mesh_id.items():
        mesh_id_to_phenotype[mesh_id] = phenotype
    for drugbank_id, diseases in drug_to_diseases.iteritems():
        for phenotype, dui, val in diseases:
            if val > 0:
                if dui in mesh_id_to_phenotype: # In the disease data set
                    disease = mesh_id_to_phenotype[dui].lower()
                    disease_to_drugs.setdefault(disease, set()).add(drugbank_id)
    return disease_to_drugs


def get_drug_disease_mapping(base_dir, selected_drugs, name_to_drug, synonym_to_drug, mesh_id_to_name, mesh_id_to_name_with_synonyms, dump_file):
    if os.path.exists(dump_file):
	drug_to_diseases = cPickle.load(open(dump_file))
	return drug_to_diseases 
    # Get mesh name to mesh id mapping
    mesh_name_to_id = {}
    for mesh_id, names in mesh_id_to_name_with_synonyms.iteritems():
        for name in names:
	    for name_mod in [ name, name.replace(",", ""), name.replace("-", " "), name.replace(",", "").replace("-", " ") ]:
		mesh_name_to_id[name_mod] = mesh_id
    # Get CT info
    drug_to_ctids = get_interventions(base_dir)
    ctid_to_conditions = get_ctid_to_conditions(base_dir)
    ctid_to_phase = get_ctid_to_phase(base_dir) 
    # Get CT - MeSH disease mapping
    intervention_to_mesh_name = {}
    interventions = reduce(lambda x,y: x|y, ctid_to_conditions.values())
    for intervention in interventions:
	if intervention.endswith('s'):
	    intervention = intervention[:-1]
	idx = intervention.find("(")
	if idx != -1:
	    intervention = intervention[:idx].rstrip()
	try:
	    exp = re.compile(r"\b%ss{,1}\b" % re.escape(intervention))
	except:
	    print "Problem with regular expression:", intervention
	for mesh_name, dui in mesh_name_to_id.iteritems():
	    m = exp.search(mesh_name)
	    if m is None: 
		continue
	    elif len(mesh_name.split()) != len(intervention.split()): # no partial overlap
		continue
	    phenotype = mesh_id_to_name[dui]
	    intervention_to_mesh_name[intervention] = phenotype
	    break
    #print len(intervention_to_mesh_name), intervention_to_mesh_name.items()[:5] 
    # Get interventions
    phase_to_value = { "Phase 0": 0.5, "Phase 1": 0.6, "Phase 1/Phase 2": 0.65, "Phase 2": 0.7, "Phase 2/Phase 3": 0.75, "Phase 3": 0.8, "Phase 3/Phase 4":0.85, "Phase 4": 0.9, "N/A": 0.5 }
    status_to_value = { "Terminated": -0.5, "Withdrawn": -1} #,"Completed", "Recruiting", "Not yet recruiting"
    drug_to_diseases = {}
    non_matching_drugs = set()
    for drug, ctids in drug_to_ctids.iteritems():
	drugbank_id = None
	if name_to_drug is None:
	    drugbank_id = drug
	else:
	    if drug in name_to_drug:
		drugbank_id = name_to_drug[drug]
	    elif drug in synonym_to_drug:
		drugbank_id = synonym_to_drug[drug]
	    else:
		non_matching_drugs.add(drug)
		continue
	if selected_drugs is not None and drugbank_id not in selected_drugs:
	    continue
	interventions = set()
	for ctid in ctids:
	    phase, status = ctid_to_phase[ctid]
	    val = 0.5
	    if phase not in phase_to_value:
		print "Unknown phase:", phase
	    if status in status_to_value and phase in phase_to_value:
		val = phase_to_value[phase] - 0.1
	    interventions |= ctid_to_conditions[ctid]
	if len(interventions) == 0:
	    continue
	for intervention in interventions:
	    if intervention not in intervention_to_mesh_name:
		continue
	    phenotype = intervention_to_mesh_name[intervention]
	    dui = mesh_name_to_id[phenotype]
	    drug_to_diseases.setdefault(drugbank_id, set()).add((phenotype, dui, val))
    #print "Non matching drugs:", len(non_matching_drugs) 
    #print len(drug_to_diseases), drug_to_diseases.items()[:5]
    cPickle.dump(drug_to_diseases, open(dump_file, 'w'))
    return drug_to_diseases


def get_ctid_to_conditions(base_dir):
    condition_file = base_dir + "conditions.txt"
    condition_file2 = base_dir + "condition_browse.txt"
    # Get conditions
    ctid_to_conditions = {} 
    f = open(condition_file)
    f.readline()
    for line in f:
	words = line.strip().split("|")
	ctid = words[1]
	condition = words[2] #.lower()
	ctid_to_conditions.setdefault(ctid, set()).add(condition)
    f.close() 
    return ctid_to_conditions
    f = open(condition_file2)
    f.readline()
    for line in f:
	words = line.strip().split("|")
	ctid = words[1]
	condition = words[2] #.lower()
	ctid_to_conditions.setdefault(ctid, set()).add(condition)
    f.close() 
    return ctid_to_conditions


def get_ctid_to_phase(base_dir):
    study_file = base_dir + "clinical_study.txt"
    # Get phase information
    ctid_to_phase = {}
    f = open(study_file)
    line = f.readline()
    words = line.strip().split("|")
    header_to_idx = dict((word.lower(), i) for i, word in enumerate(words))
    ctid_to_phase = {}
    text = None
    while line:
	line = f.readline()
	if line.startswith("NCT"):
	    if text is not None:
		words = text.strip().split("|")
		ctid = words[0]
		try:
		    phase = words[header_to_idx["phase"]]
		    status = words[header_to_idx["overall_status"]]
		except:
		    print words
		    return
		if phase.strip() != "":
		    ctid_to_phase[ctid] = (phase, status)
	    text = line
	else:
	    text += line
    f.close() 
    words = text.strip().split("|")
    ctid = words[0]
    phase = words[header_to_idx["phase"]]
    status = words[header_to_idx["overall_status"]]
    if phase.strip() != "":
	ctid_to_phase[ctid] = (phase, status)
    return ctid_to_phase


def get_interventions(base_dir): 
    #ctid_to_drugs = {}
    drug_to_ctids = {}
    intervention_file = base_dir + "interventions.txt"
    f = open(intervention_file)
    f.readline()
    prev_row = 0
    ignored_intervention_types = set()
    for line in f:
	words = line.strip().split("|")
	try:
	    row = int(words[0])
	    if row != prev_row + 1:
		continue
	except:
	    continue
	prev_row += 1
	try:
	    ctid = words[1]
	except:
	    print words
	intervention = words[2]
	drug = words[3].lower()
	drug = drug.decode("ascii", errors="ignore").encode("ascii")
	drug = drug.strip("\"'")
	if intervention != "Drug" and intervention != "Biological" :
	    ignored_intervention_types.add(intervention)
	    continue
	drug_to_ctids.setdefault(drug, set()).add(ctid)
	#ctid_to_drugs.setdefault(ctid, set()).add(drug)
	#conditions = drug_to_interventions.setdefault(drug, set())
	#conditions |= ctid_to_conditions[ctid]
    f.close()
    #print "Ignored intervention types:", ignored_intervention_types
    intervention_file = base_dir + "intervention_browse.txt"
    f = open(intervention_file)
    f.readline()
    for line in f:
	words = line.strip().split("|")
	row = int(words[0])
	ctid = words[1]
	drug = words[2].lower()
	drug = drug.decode("ascii", errors="ignore").encode("ascii")
	drug = drug.strip("\"'")
	drug_to_ctids.setdefault(drug, set()).add(ctid)
	#ctid_to_drugs.setdefault(ctid, set()).add(drug)
    f.close()
    intervention_file = base_dir + "intervention_other_names.txt"
    f = open(intervention_file)
    f.readline()
    for line in f:
	words = line.strip().split("|")
	row = int(words[0])
	ctid = words[1]
	drug = words[3].lower()
	drug = drug.decode("ascii", errors="ignore").encode("ascii")
	drug = drug.strip("\"'")
	drug_to_ctids.setdefault(drug, set()).add(ctid)
	#ctid_to_drugs.setdefault(ctid, set()).add(drug)
    f.close()
    #print set(ctid_to_phase.values())
    return drug_to_ctids #ctid_to_drugs 


def get_drug_to_interventions():
    drug_to_interventions = {}
    non_matching_drugs = set()
    for drug, ctids in drug_to_ctids.iteritems():
	drugbank_id = None
	if name_to_drug is None:
	    drugbank_id = drug
	else:
	    if drug in name_to_drug:
		drugbank_id = name_to_drug[drug]
	    elif drug in synonym_to_drug:
		drugbank_id = synonym_to_drug[drug]
	    else:
		non_matching_drugs.add(drug)
		continue
	values = set()
	for ctid in ctids:
	    #if ctid_to_phase[ctid][0] != "Phase 3":  
	    #	continue
	    values |= ctid_to_conditions[ctid]
	if len(values) == 0:
	    continue
	drug_to_interventions.setdefault(drugbank_id, values)
    #print "Non matching drugs:", len(non_matching_drugs)
    #phenotypes = disease_to_drugs.keys()
    #disease_to_interventions = {}
    #for drug, interventions in drug_to_interventions.iteritems():
    #	for intervention in interventions:
    #	    intervention = intervention.lower()
    #	    for disease in phenotypes:
    #		values = text_utilities.tokenize_disease_name(disease)
    #		if all([ intervention.find(word.strip()) != -1 for word in values ]): # disease.split(",") ]):
    #		    disease_to_drugs_ct.setdefault(disease, set()).add(drug)
    #		    disease_to_interventions.setdefault(disease, set()).add(intervention)
    #for disease, interventions in disease_to_interventions.iteritems():
    #	print disease, interventions
    #print len(drug_to_interventions), drug_to_interventions.items()[:5]
    #print drug_to_ctids["voriconazole"], print ctid_to_conditions["NCT00005912"], print ctid_to_phase["NCT00005912"]
    #print drug_to_interventions["DB00582"]
    return drug_to_interventions


def get_frequent_interventions(drug_to_interventions):
    condition_to_count = {}
    for drug, interventions in drug_to_interventions.iteritems():
	for condition in interventions:
	    if condition in condition_to_count:
		condition_to_count[condition] += 1
	    else:
		condition_to_count[condition] = 1
    values = []
    for condition, count in condition_to_count.iteritems():
	values.append((count, condition))
    values.sort()
    values.reverse()
    #print values[:50]
    return values


