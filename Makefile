.PHONY: spectrum-quality data env
CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Start the spectrum quality notebook
spectrum-quality: notebooks/spectrum-quality
	${CONDA_ACTIVATE} $@ && cd $< && \
		jupyter lab --port 8999

## Create the data for the spectrum quality task.
## This will download a bunch of mzML files and
## search them with Sage.
spectrum-quality-data: data/spectrum-quality.tar.gz

env: env.yml
	conda env update -f env.yml --prune

data/spectrum-quality.tar.gz: bin/sage data/manual/sage.json data/fasta/human.fasta scripts/sage-search.py
	${CONDA_ACTIVATE} 2024_depthcharge-demos \
		&& python scripts/sage-search.py -s 42 10 5 5
	tar czf data/spectrum-quality.tar.gz data/spectrum-quality

data/fasta/human.fasta:
	mkdir -p data/fasta
	curl -sL "https://rest.uniprot.org/uniprotkb/stream?compressed=true&format=fasta&query=%28%28proteome%3AUP000005640%29+AND+reviewed%3Dtrue%29" \
    | gunzip -c > data/fasta/human.fasta

bin/sage:
	mkdir -p bin
	curl -sL https://github.com/lazear/sage/releases/download/v0.14.7/sage-v0.14.7-x86_64-unknown-linux-gnu.tar.gz \
		| tar xzfO /dev/stdin sage-*/sage > bin/sage
	chmod u+x bin/sage

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
