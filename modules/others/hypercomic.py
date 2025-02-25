import random

from modules import Minter, Logger, RequestClient, Client
from config import HYPERCOMIC_ABI
from modules.interfaces import SoftwareException
from utils.tools import helper, gas_checker, sleep
from settings import HYPERCOMIC_NFT_ID


class HyperComic(Minter, Logger, RequestClient):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        RequestClient.__init__(self, client)

    async def get_tx_data(self, nft_id: int):
        url = f'https://play.hypercomic.io/Claim/actionZK/conditionsCheck2'

        nonce = await self.client.w3.eth.get_transaction_count(self.client.address)
        address = self.client.address.lower()

        payload = f'trancnt={nonce}&walletgbn=Metamask&wallet={address}&nftNumber={nft_id}'

        headers = {
            "authority": "play.hypercomic.io",
            "method": "POST",
            "path": "/Claim/actionZK/conditionsCheck2",
            "scheme": "https",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
            #"Content-Length": "92",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://zk24.hypercomic.io",
            "Referer": "https://zk24.hypercomic.io/",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Microsoft Edge";v="121", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "Windows",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

        response = await self.client.session.post(url=url, headers=headers, data=payload)
        if response.status == 200:
            return await response.text()
        raise SoftwareException('Bad response from HyperComic API')

    @helper
    @gas_checker
    async def mint(self):
        mint_info = {
            1: (6, '0x9d405d767b5d2c3F6E2ffBFE07589c468d3fc04E', 'zkDmail Explorer'),
            2: (7, '0x02E1eb4547A6869da1e416cfd5916C213655aA24', 'zkSync Bridger'),
            3: (8, '0x9f5417Dc26622A4804Aa4852dfBf75Db6f8c6F9F', 'zkSync Root'),
            4: (9, '0x761cCCE4a16A670Db9527b1A17eCa4216507946f', 'zkSync Junior'),
        }

        mint_ids = list(HYPERCOMIC_NFT_ID if HYPERCOMIC_NFT_ID != 0 else [random.choice([1, 2, 3, 4])])

        random.shuffle(mint_ids)

        result_list = []
        for mint_id in mint_ids:
            nft_id = mint_info[mint_id][0]
            contract_address = mint_info[mint_id][1]
            nft_name = mint_info[mint_id][2]
            try:

                calldata = await self.get_tx_data(nft_id)

                if calldata == 'notEnough':
                    self.logger_msg(
                        *self.client.acc_info, msg=f"Not eligible for mint {nft_name} NFT.", type_msg='warning')
                    continue

                contract = self.client.get_contract(contract_address, HYPERCOMIC_ABI)

                self.logger_msg(*self.client.acc_info, msg=f"Mint {nft_name} NFT. Price: 0.00012 ETH")

                transaction = await contract.functions.mint(
                    calldata.strip()
                ).build_transaction(await self.client.prepare_transaction(value=120000000000000))

                result_list.append(await self.client.send_transaction(transaction))

                await sleep(self)
            except Exception as error:
                raise SoftwareException(f'Can`t mint {nft_name}. Error: {error}')

        return all(result_list)
