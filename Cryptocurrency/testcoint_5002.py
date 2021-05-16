# Create Cryptocurrency

import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Create Blockchain

class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
        
    def create_block(self, proof, previous_hash):
        block = { 'index': len(self.chain) + 1,
                  'timestamp': str(datetime.datetime.now()),
                  'proof': proof,
                  'previous_hash': previous_hash,
                  'transactions': self.transactions}
        self.transactions = [];
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operations = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operations[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys= True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operations = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operations[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender,
                                   'receiver': receiver,
                                   'amount': amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length  and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
            
            
            
# Initailize Flask
app = Flask(__name__)

# Creating an addres for the node on Port 5000
node_address = str(uuid4()).replace('-', '')

# Initialize Blockchain object
blockchain = Blockchain()

# Mining a new block
@app.route('/mine-block', methods = [ 'GET' ])
def mine_block():
    previous_block = blockchain.get_previous_block()
    proof = blockchain.proof_of_work(previous_block['proof'])
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, receiver = 'USER 2', amount = 100)
    block = blockchain.create_block(proof, previous_hash)
    response = { 'message': 'Congratulations, you just mined a block!',
                 'index': block['index'],
                 'timestamp': block['timestamp'],
                 'proof': block['proof'],
                 'transactions': block['transactions'],
                 'previous_hash': block['previous_hash'] }
    return jsonify(response), 200

# Get Full Blockchain
@app.route('/chain', methods = [ 'GET' ])
def chain():
    response = { 'chain' : blockchain.chain,
                 'length': len(blockchain.chain) }
    return jsonify(response), 200

# check if chain is valid
@app.route('/is-valid-chain', methods = [ 'GET' ])
def is_valid_chain():
    valid = blockchain.is_chain_valid(blockchain.chain)
    response = { 'valid': valid }
    return jsonify(response), 200

# Add Transaction to the blockchain
@app.route('/add-transaction', method = [ 'POST' ])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in json for key in transaction_keys):
        return "Missing Key In Transaction", 400
    block_index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'This transaction will be added to Block {block_index}'}
    return jsonify(response), 201

# Connect new node
@app.route('/connect-node', method = [ 'POST' ])
def connect_node():
    json = request.get_json()
    node_addresses = json['nodes']
    if node_addresses is None:
        return "No Node Address Found", 400
    for node in node_addresses:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now connected',
               'total_node': list(blockchain.nodes)}
    return jsonify(response), 

# Replace the chain by the longest chain if needed
@app.route('/replace-chain', method = [ 'GET' ])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    response = { 'replaced': is_chain_replaced(), 'actual_chain': blockchain.chain }
    return jsonify(response), 200

app.run(host = '0.0.0.0', port = 5000)
        
        
        
        