#!/usr/bin/env python3
import logging
import ot
import util
import yao
from abc import ABC, abstractmethod
from requirements import saveSet,verifyOperation,askForInput,intToBin,binToInt

logging.basicConfig(format="[%(levelname)s] %(message)s",
                    level=logging.WARNING)


class YaoGarbler(ABC):
    """An abstract class for Yao garblers (e.g. Alice)."""
    def __init__(self, circuits):
        circuits = util.parse_json(circuits)
        self.name = circuits["name"]
        self.circuits = []

        for circuit in circuits["circuits"]:
            garbled_circuit = yao.GarbledCircuit(circuit)
            pbits = garbled_circuit.get_pbits()
            entry = {
                "circuit": circuit,
                "garbled_circuit": garbled_circuit,
                "garbled_tables": garbled_circuit.get_garbled_tables(),
                "keys": garbled_circuit.get_keys(),
                "pbits": pbits,
                "pbits_out": {w: pbits[w]
                              for w in circuit["out"]},
            }
            self.circuits.append(entry)

    @abstractmethod
    def start(self):
        pass


class Alice(YaoGarbler):
    """Alice is the creator of the Yao circuit.

    Alice creates a Yao circuit and sends it to the evaluator along with her
    encrypted inputs. Alice will finally print the truth table of the circuit
    for all combination of Alice-Bob inputs.

    Alice does not know Bob's inputs but for the purpose
    of printing the truth table only, Alice assumes that Bob's inputs follow
    a specific order.

    Attributes:
        circuits: the JSON file containing circuits
        oblivious_transfer: Optional; enable the Oblivious Transfer protocol
            (True by default).
    """
    def __init__(self, circuits, oblivious_transfer=True):
        super().__init__(circuits)
        self.socket = util.GarblerSocket()
        self.ot = ot.ObliviousTransfer(self.socket, enabled=oblivious_transfer)
        self.set = []
        self.result = 0

    def start(self):
        """Start Yao protocol."""
        for circuit in self.circuits:
            to_send = {
                "circuit": circuit["circuit"],
                "garbled_tables": circuit["garbled_tables"],
                "pbits_out": circuit["pbits_out"],
            }
            logging.debug(f"Sending {circuit['circuit']['id']}")
            self.socket.send_wait(to_send)
            #ask for set and save it locally (for later check)
            self.set = askForInput("a")
            saveSet(self.set,"a")  #save set to a file
            self.print(circuit) #print the circuit and obtain the result
            res = verifyOperation(self.result)   #verify the result
            if res == 1:
                msg = f"\nThe sum has been done correctly, result is {self.result}."
            else:
                msg = f"\nAn error occured during MPC calculation, however the obtained result is {self.result}, which is not correct."
            print(msg)  #this message, containing the result must be sent to Bob
            self.sendResultToBob(msg)

    def sendResultToBob(self,msg):
        """Sends the result to Bob

        Args:
            msg: The message that must be sent.
        """
        self.socket.send(msg) 
        #print("Message sent to Bob")    #only for debugging
        

    def print(self, entry):
        """Print circuit evaluation for all Bob and Alice inputs.

        Args:
            entry: A dict representing the circuit to evaluate.
        """
        circuit, pbits, keys = entry["circuit"], entry["pbits"], entry["keys"]
        
        outputs = circuit["out"]
        a_wires = circuit.get("alice", [])  # Alice's wires (input bits)
        a_inputs = {}  # map from Alice's wires to (key, encr_bit) inputs
        b_wires = circuit.get("bob", [])  # Bob's wires
        b_keys = {  # map from Bob's wires to a pair (key, encr_bit)
            w: self._get_encr_bits(pbits[w], key0, key1)
            for w, (key0, key1) in keys.items() if w in b_wires
        }
        
        bits_a = list(intToBin(sum(self.set))) # Alice's inputs, adapt size to 8 bit with 2-complement
        bits_a = [int(i) for i in bits_a]   #convert in a list of int
        print(bits_a)
        
        # Map Alice's wires to (key, encr_bit)
        for i in range(len(a_wires)):
            a_inputs[a_wires[i]] = (keys[a_wires[i]][bits_a[i]],
                                    pbits[a_wires[i]] ^ bits_a[i])

        print(f"\n======== {circuit['id']} ========\n")
        
        # Send Alice's encrypted inputs and keys to OT
        result = self.ot.get_result(a_inputs, b_keys)

        # Format output
        str_bits_a = ' '.join([str(i) for i in bits_a][:len(a_wires)])
        str_result = ' '.join([str(result[w]) for w in outputs])#.replace(" ", "")
        print("Values of the computation\n")
        print("Syntax: parties/result:  [list of bits] = [correspective values]\n")
        print(f"Alice: {a_wires} = {str_bits_a} \n"
              f"Computed result by circuit: {outputs} = {str_result}")
        
        self.result = binToInt(str_result.replace(" ", ""))  #result converted in decimal base, i remove white spaces
        
    def _print_tables(self, entry):
        """Print garbled tables."""
        entry["garbled_circuit"].print_garbled_tables()
        
    def _get_encr_bits(self, pbit, key0, key1):
        return ((key0, 0 ^ pbit), (key1, 1 ^ pbit))


class Bob:
    """Bob is the receiver and evaluator of the Yao circuit.

    Bob receives the Yao circuit from Alice, computes the results and sends
    them back.

    Args:
        oblivious_transfer: Optional; enable the Oblivious Transfer protocol
            (True by default).
    """
    def __init__(self, oblivious_transfer=True):
        self.socket = util.EvaluatorSocket()
        self.ot = ot.ObliviousTransfer(self.socket, enabled=oblivious_transfer)

    def listen(self):
        """Start listening for Alice messages."""
        logging.info("Start listening")
        try:
            for entry in self.socket.poll_socket():
                self.socket.send(True)
                self.set = askForInput("b") # Ask for input, via console
                saveSet(self.set,"b")   #save the set in a file
                self.send_evaluation(entry) #send evalution using OT
                self.printResult() #print the final result, received from Alice
                break   #bob does only a single run, used to avoid socket problems
        except KeyboardInterrupt:
            logging.info("Stop listening")

    def send_evaluation(self, entry):
        """Evaluate yao circuit for all Bob and Alice's inputs and
        send back the results.

        Args:
            entry: A dict representing the circuit to evaluate.
        """
        circuit, pbits_out = entry["circuit"], entry["pbits_out"]
        garbled_tables = entry["garbled_tables"]
        b_wires = circuit.get("bob", [])  # list of Bob's wires

        print(f"Received {circuit['id']}")
        
        bits_b = list(intToBin(sum(self.set))) # Bob's inputs, adapt size to 8 bit with 2-complement
        bits_b = [int(i) for i in bits_b]   #convert in a list of int
        print(bits_b)

        # Create dict mapping each wire of Bob to Bob's input
        b_inputs_clear = {
            b_wires[i]: bits_b[i]
            for i in range(len(b_wires))
        }
        
        str_bits_b = ' '.join([str(i) for i in bits_b][:len(b_wires)])
        print("\nSyntax:  parties/result  [list of bits] = [correspective values]\n")
        print(f"Bob {b_wires} = {str_bits_b}\n")

        # Evaluate and send result to Alice
        self.ot.send_result(circuit, garbled_tables, pbits_out,
                            b_inputs_clear)
    
    def printResult(self):
        """Function that permits Bob to print the computed result, it waits until Alice sends the final result to him and then print it out
        
        """
        print(self.socket.receive())


def main(
    party,
    circuit_path="circuits/add.json",
    oblivious_transfer=True,
    print_mode="circuit",
    loglevel=logging.WARNING,
):
    logging.getLogger().setLevel(loglevel)

    if party == "alice":
        alice = Alice(circuit_path, oblivious_transfer=oblivious_transfer)
        alice.start()
    elif party == "bob":
        bob = Bob(oblivious_transfer=oblivious_transfer)
        bob.listen()
    else:
        logging.error(f"Unknown party '{party}'")


if __name__ == '__main__':
    import argparse

    def init():
        loglevels = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }

        parser = argparse.ArgumentParser(description="Run Yao protocol.")
        parser.add_argument("party",
                            choices=["alice", "bob"],
                            help="the yao party to run")
        parser.add_argument(
            "-c",
            "--circuit",
            metavar="circuit.json",
            default="circuits/default.json",
            help=("the JSON circuit file for alice"),
        )
        parser.add_argument("--no-oblivious-transfer",
                            action="store_true",
                            help="disable oblivious transfer")
        parser.add_argument(
            "-m",
            metavar="mode",
            choices=["circuit", "table"],
            default="circuit",
            help="the print mode for local tests (default 'circuit')")
        parser.add_argument("-l",
                            "--loglevel",
                            metavar="level",
                            choices=loglevels.keys(),
                            default="warning",
                            help="the log level (default 'warning')")

        main(
            party=parser.parse_args().party,
            circuit_path=parser.parse_args().circuit,
            oblivious_transfer=not parser.parse_args().no_oblivious_transfer,
            print_mode=parser.parse_args().m,
            loglevel=loglevels[parser.parse_args().loglevel],
        )

    init()
