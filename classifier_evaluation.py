from toolbox import guild_utilities, selection_utilities

def create_R_script(file_name, absolute_dir, title=None, only=None, show_spread=False, append=False):
    if title is not None:
	plot_title = title
    if append:
	f = open(file_name, "a") 
    else:
	f = open(file_name, "w") 
    f.write("library(ROCR)\n") 
    f.write("v<-read.table(\"%spredictions.dat\")\n" % absolute_dir) 
    f.write("l<-read.table(\"%slabels.dat\")\n" % absolute_dir)
    f.write("pred<-prediction(v, l)\n")
    f.write("average<-function(vals) {\n")
    f.write("\tm<-matrix(sapply(vals, function(x){mean(x)}),nrow=length(vals),byrow=T)\n")
    f.write("\tm[m==Inf]<-NA\n")
    f.write("\tmax(colMeans(m),na.rm=T)\n")
    f.write("}\n")
    if only == "auc":
	f.write("perfAUC<-performance(pred, \"auc\")\n")
	f.write("e=c(); n=c(); x=0; for ( i in perfAUC@y.values ) { x<-x+1;  e[x] <- i; n[x]<-x }\n")
	if append:
	    f.write("sink(\"%s%s_auc.txt\", append=TRUE, split=TRUE)\n" % (absolute_dir, title))
	else:
	    f.write("sink(\"%sauc.txt\", append=TRUE, split=TRUE)\n" % absolute_dir)
	f.write("paste(format(mean(e), digits=3), format(sd(e), digits=3), sep=\" \")\n") 
	f.write("sink()\n")
	f.close()
	return
    elif only == "cutoff":
	if title is None:
	    plot_title = "Precision vs Sensitivity"
	f.write("perfPPV<-performance(pred, \"ppv\")\n")
	f.write("perfSens<-performance(pred, \"sens\")\n")
	if show_spread:
	    f.write("d<-average(perfPPV@x.values)\n")
	    f.write("plot(perfPPV, lwd=2, col=2, ylab=\"Percentage\", main=\"%s\", avg=\"vertical\", plotCI.col=2, spread.estimate=\"stddev\", show.spread.at=seq(0,d,by=d/6))\n" % plot_title)
	else:
	    f.write("plot(perfPPV, lwd=2, col=2, ylab=\"Percentage\", main=\"%s\", avg=\"vertical\")\n" % plot_title)
	if show_spread:
	    f.write("d<-average(perfSens@x.values)\n")
	    f.write("plot(perfSens, lwd=2, col=3, avg=\"vertical\", plotCI.col=3, spread.estimate=\"stddev\", show.spread.at=seq(0,d,by=d/6), add=TRUE)\n") 
	else:
	    f.write("plot(perfSens, lwd=2, col=3, avg=\"vertical\", add=TRUE)\n") 
	f.write("perf<-performance(pred, \"prbe\")\n")
	f.write("legend(\"bottomright\", c(\"Precision\", \"Sensitivity\", paste(\"(\", format(average(perf@x.values), digits=2), format(average(perf@y.values), digits=2), \")\", sep=\" \")), lty=c(1,1,0), col=c(2,3,1))\n")
	f.close()
	return
    # ROC
    f.write("perfROC<-performance(pred, \"tpr\", \"fpr\")\n")
    f.write("png(\"%sroc.png\")\n" % absolute_dir)
    if title is None:
	plot_title = "ROC curve"
    if show_spread:
	f.write("plot(perfROC, lwd=2, col=2, xlab=\"False Positive Rate\", ylab=\"True Positive Rate\", main=\"%s\", avg=\"vertical\", plotCI.col=2, spread.estimate=\"stddev\", show.spread.at=seq(0,1,by=0.20))\n" % plot_title)
    else:
	f.write("plot(perfROC, lwd=2, col=2, xlab=\"False Positive Rate\", ylab=\"True Positive Rate\", main=\"%s\", avg=\"vertical\")\n" % plot_title)
    f.write("legend(\"bottomright\", c(\"(Avg. over xval folds)\"), lty=c(1), col=c(2))\n") 
    f.write("dev.off()\n")
    # Cutoff (PPV - Sens)
    f.write("perfPPV<-performance(pred, \"ppv\")\n")
    f.write("perfSens<-performance(pred, \"sens\")\n")
    f.write("png(\"%scutoff.png\")\n" % absolute_dir)
    if title is None:
	plot_title = "Precision vs Sensitivity"
    if show_spread:
	f.write("d<-average(perfPPV@x.values)\n")
	f.write("plot(perfPPV, lwd=2, col=2, ylab=\"Percentage\", main=\"%s\", avg=\"vertical\", plotCI.col=2, spread.estimate=\"stddev\", show.spread.at=seq(0,d,by=d/6))\n" % plot_title)
    else:
	f.write("plot(perfPPV, lwd=2, col=2, ylab=\"Percentage\", main=\"%s\", avg=\"vertical\")\n" % plot_title)
    if show_spread:
	f.write("d<-average(perfSens@x.values)\n")
	f.write("plot(perfSens, lwd=2, col=3, avg=\"vertical\", plotCI.col=3, spread.estimate=\"stddev\", show.spread.at=seq(0,d,by=d/6), add=TRUE)\n") 
    else:
	f.write("plot(perfSens, lwd=2, col=3, avg=\"vertical\", add=TRUE)\n") 
    f.write("perf<-performance(pred, \"prbe\")\n")
    f.write("legend(\"bottomright\", c(\"Precision\", \"Sensitivity\", paste(\"(\", format(average(perf@x.values), digits=2), format(average(perf@y.values), digits=2), \")\", sep=\" \")), lty=c(1,1,0), col=c(2,3,1))\n") 
    f.write("dev.off()\n")
    # AUC
    if title is None:
	plot_title = "Area Under ROC Curve (AUC)"
    f.write("png(\"%sauc.png\")\n" % absolute_dir)
    f.write("perfAUC<-performance(pred, \"auc\")\n")
    f.write("e=c(); n=c(); x=0; for ( i in perfAUC@y.values ) { x<-x+1;  e[x] <- i; n[x]<-x }; barplot(e, names=n, ylim=c(0,1),ylab= \"AUC\",xlab=\"Fold\", main=\"%s\")\n" % plot_title)
    f.write("legend(\"topright\", c(paste(\"(Avg: \", format(mean(e), digits=3), \")\",sep=\"\")), lty=c(), col=c())\n") 
    f.write("dev.off()\n")
    f.write("sink(\"%sauc.txt\", append=TRUE, split=TRUE)\n" % absolute_dir)
    f.write("paste(format(mean(e), digits=3), format(sd(e), digits=3), sep=\" \")\n") 
    f.write("sink()\n")
    f.close()
    #os.system("R CMD BATCH %s" % "*.R") 
    return

def create_ROCR_files(list_node_scores_and_labels, file_predictions, file_labels):
    """
	list_node_scores_and_labels: list of node (score, label) tuple (corresponding to each validation node) list (corresponding to xval fold)
    """
    f_pred = open(file_predictions, 'w')
    f_lab = open(file_labels, 'w')
    firstTime = True
    for i, node_scores_and_labels in enumerate(zip(*list_node_scores_and_labels)):
	if i == 0:
            for j in xrange(len(node_scores_and_labels)):
                f_pred.write("\tFold" + str(j+1))  
                f_lab.write("\tFold" + str(j+1))  
            f_pred.write("\n")  
            f_lab.write("\n")  
        f_pred.write("%d"%(i+1))
        f_lab.write("%d"%(i+1))
        for (score, label) in node_scores_and_labels:
            f_pred.write("\t" + str(score))
            f_lab.write("\t" + str(label))
        f_pred.write("\n")
        f_lab.write("\n")
    f_pred.close()
    f_lab.close()
    return


def get_validation_node_scores_and_labels(file_result, file_seed_test_scores, file_node_scores, n_random_negative_folds = None, n_negatives = None, default_score = 0, replicable = 123, candidates_file = None, previous_negative_sample_size=None):
    """
	Returns a list of scores and labels [ ([0-1], [01]) ] for validation
	file_result: File to parse output scores 
	file_seed_test_scores: File to parse test seeds
	file_node_scores: File to parse all non seeds
	n_negatives: Number of negative instanaces
		     If None the same as number of test nodes
	n_random_negative_folds: Number of non-seed scores to be averaged to be assigned as negative instance
				 If None calculated to cover as much as non-seed scores as possible
				 If 0 all negative data is used
	default_score: All nodes that have a higher score than this score in file_node_scores will be considered as seeds
    """
    from guild_utilities import get_node_to_score, get_nodes
    from selection_utilities import generate_samples_from_list_without_replacement

    node_to_score = get_node_to_score(file_result)
    test_nodes = get_nodes(file_seed_test_scores)
    initial_to_score = get_node_to_score(file_node_scores)
    non_seeds = set([ node for node, score in initial_to_score.iteritems() if score==default_score ])
    node_validation_data = [ (node_to_score[node], 1) for node in test_nodes ] 

    if candidates_file is not None:
	candidates = get_nodes(candidates_file)
	node_to_score = dict([ (node, node_to_score[node]) for node in candidates ])
	non_seeds = list(non_seeds & candidates)

    if n_random_negative_folds == 0:
	negative_sample_size = None
	node_validation_data.extend([(node_to_score[node], 0) for node in set(node_to_score.keys()) & non_seeds ])
    else:
	n_actual_folds = 0
	if n_negatives is None:
	    n_negatives = len(test_nodes)
	negative_sample_size = n_negatives 
	if previous_negative_sample_size is not None: 
	    if previous_negative_sample_size > negative_sample_size:
		negative_sample_size = previous_negative_sample_size 
	negative_scores = [ 0 ] * negative_sample_size 
	non_seeds = list(non_seeds)
	for sample in generate_samples_from_list_without_replacement(non_seeds, negative_sample_size, n_random_negative_folds, replicable = replicable):
	    for i, node in enumerate(sample):
		negative_scores[i] += node_to_score[node] 
	    n_actual_folds += 1
	node_validation_data.extend(map(lambda x: (x/n_actual_folds, 0), negative_scores))
    return node_validation_data, negative_sample_size


def calculate_performance_metric_counts_using_random_negatives(node_to_score, setNodeTest, non_seeds, score_threshold, n_random_negative_folds = None, replicable=123):
    from selection_utilities import generate_samples_from_list_without_replacement

    (nTP, nFP, nFN, nTN) = (0.0, 0.0, 0.0, 0.0)
    for id, score in node_to_score.iteritems(): # if candidates based - for each candidate
        if id in setNodeTest: # in the initial association file
            if score >= score_threshold:
                nTP += 1
            else:
                nFN += 1

    if n_random_negative_folds == 0:
	for id, score in node_to_score.iteritems():
	    if id in non_seeds:
		if score >= score_threshold:
		    nFP += 1
		else:
		    nTN += 1
    else:
	n_actual_folds = 0
	for sample in generate_samples_from_list_without_replacement(non_seeds, len(setNodeTest), n_random_negative_folds, replicable = replicable):
	    setNegative = set(sample)
	    n_actual_folds += 1
	    for id, score in node_to_score.iteritems():
		if id in setNegative:
		    if score >= score_threshold:
			nFP += 1
		    else:
			nTN += 1
	nFP /= n_actual_folds
	nTN /= n_actual_folds
    return (nTP, nFP, nFN, nTN)

def calculatePerformance(nTP, nFP, nFN, nTN):
    try:
	acc = (nTP + nTN) / (nTP + nFP + nTN + nFN)
    except ZeroDivisionError:
	acc = None
    try:
        sens = nTP / (nTP + nFN)
    except:
        sens = None
    try:
        spec = nTN / (nTN + nFP)
    except:
        spec = None
    try:
        ppv = nTP / (nTP + nFP)
    except:
        ppv = None

    #if spec is not None:
    #    return (sens, (1-spec))
    #else:
    #    return (sens, None)

    return (acc, sens, spec, ppv)


