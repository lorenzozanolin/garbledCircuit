ALICE = python3 code/main.py alice  # circuit generator (client)
BOB = python3 code/main.py bob      # circuit evaluator (server)
ONEFILE = ${ALICE}             # choose ALICE

default:
	@echo 'Usage 1: make {alice, bob}'
	@echo 'Usage 2: make {circuit}'

clean:
	rm -rf __pycache__

alice:
	${ALICE} -c circuits/add.json

bob:
	${BOB}

add:
	${ONEFILE} -c circuits/add.json
