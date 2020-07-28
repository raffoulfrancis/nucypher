"""
 This file is part of nucypher.

 nucypher is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 nucypher is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with nucypher.  If not, see <https://www.gnu.org/licenses/>.
"""

import json
from pathlib import Path
from typing import Iterable, Tuple, Union, List, Dict

from eth_typing import ChecksumAddress, HexStr
from eth_utils import to_canonical_address
from web3 import Web3
from web3.contract import Contract, ContractFunction

from nucypher.blockchain.eth.constants import TOKEN_MANAGER_CONTRACT_NAME
from nucypher.blockchain.eth.interfaces import BlockchainInterfaceFactory


class Translator:  # TODO: Not sure about this name, tbh
    """Base class for Translators"""
    contract_name: str = NotImplemented

    def __init__(self, address: str, provider_uri: str = None):
        self.blockchain = BlockchainInterfaceFactory.get_or_create_interface(provider_uri=provider_uri)
        self.contract: Contract = self.blockchain.get_contract_instance(contract_name=self.contract_name,
                                                                        address=address)


class TokenManagerTranslator(Translator):

    contract_name = TOKEN_MANAGER_CONTRACT_NAME

    def mint(self, receiver_address: ChecksumAddress, amount: int) -> ContractFunction:
        function_call = self.contract.functions.mint(receiver_address, amount)
        return function_call

    def issue(self, amount: int) -> ContractFunction:
        function_call = self.contract.functions.issue(amount)
        return function_call

    def assign(self, receiver_address: ChecksumAddress, amount: int) -> ContractFunction:
        function_call = self.contract.functions.assign(receiver_address, amount)
        return function_call

    def burn(self, holder_address: ChecksumAddress, amount: int) -> ContractFunction:
        function_call = self.contract.functions.burn(holder_address, amount)
        return function_call


Action = Tuple[ChecksumAddress, Union[ContractFunction, HexStr, bytes]]


class CallScriptCodec:

    CALLSCRIPT_ID = Web3.toBytes(hexstr='0x00000001')

    @classmethod
    def encode_actions(cls, actions: Iterable[Action]) -> bytes:
        callscript = [cls.CALLSCRIPT_ID]

        actions = cls._format_actions(actions=actions)
        for target, action_data in actions:
            encoded_action = (to_canonical_address(target),
                              len(action_data).to_bytes(4, 'big'),
                              action_data)
            callscript.extend(encoded_action)

        callscript_data = b''.join(callscript)
        return callscript_data

    @classmethod
    def _format_actions(cls, actions: Iterable[Action]) -> Iterable[Tuple[ChecksumAddress, bytes]]:
        actions_bytes = list()
        for target, function_call in actions:
            try:
                encoded_action = function_call._encode_transaction_data()
            except AttributeError:
                encoded_action = function_call

            try:
                action_bytes = Web3.toBytes(hexstr=encoded_action)
            except TypeError:
                action_bytes = encoded_action

            actions_bytes.append((target, action_bytes))

        return actions_bytes


class Artifact:
    _HERE = Path(__file__).parent
    _ARTIFACTS_DIR = _HERE / "aragon_artifacts"

    def __init__(self, name: str):
        artifact_filepath = self._ARTIFACTS_DIR / f"{name}.json"
        with open(artifact_filepath, 'r') as artifact_file:
            self.raw_data = json.load(artifact_file)

    @property
    def abi(self) -> List[Dict]:
        return self.raw_data["abi"]
