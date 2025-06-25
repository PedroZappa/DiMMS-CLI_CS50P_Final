#==============================================================================#
#                                  MAKE CONFIG                                 #
#==============================================================================#

MAKE	= make --no-print-directory
SHELL	:= bash --rcfile ~/.bashrc

#==============================================================================#
#                                     NAMES                                    #
#==============================================================================#

NAME = CS50P_Final
VENV = .venv
MAIN = project.py
MAIN_TEST = test_project.py
EXEC = ./scripts/run.sh && python3 $(MAIN)

### Message Vars
_SUCCESS			= [$(GRN)SUCCESS$(D)]
_INFO					= [$(BLU)INFO$(D)]
_NORM_SUCCESS = $(GRN)=== OK:$(D)
_NORM_INFO 		= $(BLU)File no:$(D)
_NORM_ERR 		= $(RED)=== KO:$(D)
_SEP					= =====================

#==============================================================================#
#                                COMMANDS                                      #
#==============================================================================#

### Core Utils
RM		= rm -rf
MKDIR_P	= mkdir -p

#==============================================================================#
#                                  RULES                                       #
#==============================================================================#

##@ Project Scaffolding 󰛵

all: 	## Build and run project
	$(MAKE) run

run:	## Run project
	@if [ ! -d "$(VENV)" ]; then \
		$(MAKE) build; \
	fi
	@echo "* $(MAG)$(NAME) $(YEL)executing$(D): $(_SUCCESS)"
	@echo "$(GRN)$(_SEP)$(D)"
	@source $(EXEC)
	@echo "$(GRN)$(_SEP)$(D)"
	@echo "* $(MAG)$(NAME) $(YEL)finished$(D):"

build:	## Build project
	@echo "* $(MAG)$(NAME) $(YEL)building$(D): $(_SUCCESS)"
	source ./scripts/build.sh
	echo "* $(MAG)$(NAME) $(YEL)finished building$(D):"

##@ Utility Rules 

black:		## Run black formatter
	black $(MAIN)

##@ Test/Debug Rules 

test:		## Run tests
	pytest $(MAIN_TEST)

mypy:		## Run mypy static checker
	mypy $(MAIN)

##@ Clean-up Rules 󰃢

clean: 	## Remove object files
	@echo "*** $(YEL)Removing $(MAG)$(NAME)$(D) and deps $(YEL)object files$(D)"
	@if [ -d "$(VENV)" ]; then \
		if [ -d "$(VENV)" ]; then \
			$(RM) $(VENV); \
			$(RM) *.sqlite; \
			$(RM) "app/__pycache__"; \
			$(RM) "app/LookinSlack.egg-info"; \
			echo "*** $(YEL)Removing $(CYA)$(BUILD_PATH)$(D) folder & files$(D): $(_SUCCESS)"; \
		fi; \
	else \
		echo " $(RED)$(D) [$(GRN)Nothing to clean!$(D)]"; \
	fi

##@ Help 󰛵

help: 	## Display this help page
	@awk 'BEGIN {FS = ":.*##"; \
			printf "\n=> Usage:\n\tmake $(GRN)<target>$(D)\n"} \
		/^[a-zA-Z_0-9-]+:.*?##/ { \
			printf "\t$(GRN)%-18s$(D) %s\n", $$1, $$2 } \
		/^##@/ { \
			printf "\n=> %s\n", substr($$0, 5) } ' Makefile
## Tweaked from source:
### https://www.padok.fr/en/blog/beautiful-makefile-awk

.PHONY: create_venv source_venv

#==============================================================================#
#                                  UTILS                                       #
#==============================================================================#

# Colors
#
# Run the following command to get list of available colors
# bash -c 'for c in {0..255}; do tput setaf $c; tput setaf $c | cat -v; echo =$c; done'
#
B  		= $(shell tput bold)
BLA		= $(shell tput setaf 0)
RED		= $(shell tput setaf 1)
GRN		= $(shell tput setaf 2)
YEL		= $(shell tput setaf 3)
BLU		= $(shell tput setaf 4)
MAG		= $(shell tput setaf 5)
CYA		= $(shell tput setaf 6)
WHI		= $(shell tput setaf 7)
GRE		= $(shell tput setaf 8)
BRED 	= $(shell tput setaf 9)
BGRN	= $(shell tput setaf 10)
BYEL	= $(shell tput setaf 11)
BBLU	= $(shell tput setaf 12)
BMAG	= $(shell tput setaf 13)
BCYA	= $(shell tput setaf 14)
BWHI	= $(shell tput setaf 15)
D 		= $(shell tput sgr0)
BEL 	= $(shell tput bel)
CLR 	= $(shell tput el 1)


