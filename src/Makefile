ALICE = python3 code/main.py alice  # circuit generator (client)
BOB = python3 code/main.py bob      # circuit evaluator (server)
LOCAL = python3 code/main.py local  # local tests
ONEFILE = ${ALICE}             # choose ALICE or LOCAL

default:
	@echo 'Usage 1: make {alice, bob, local}'
	@echo 'Usage 2: make {circuit}'

clean:
	rm -rf __pycache__

alice:
	${ALICE} -c circuits/add.json

bob:
	${BOB}

local:
	${LOCAL} -c circuits/add.json

add:
	${ONEFILE} -c circuits/add.json
