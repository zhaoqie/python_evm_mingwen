# coding=utf-8
import logzero
import os
import time
from logzero import logger

"""
init
"""

file_name = "___".join(
    ["z_", os.path.split(__file__)[-1], str(time.strftime('%Y_%m_%d_%H_%M_%S'))])
log_file = file_name + ".log"
logzero.logfile(log_file)

from web3 import Web3, HTTPProvider, Account
from web3.middleware import geth_poa_middleware

# 分身1
private_key = "私钥"
recipient_address = "地址"

# 铭文格式数据
data = 'data:,{"p":"prc-20","op":"mint","tick":"pols","amt":"100000000"}'

rpc_map = {
    'mainnet': '节点url',
}


def get_transaction_eip1559(rpc_url, text_data, fee_input, get_fee_realtime=True):
    web3 = Web3(HTTPProvider(rpc_url))

    web3.middleware_onion.inject(geth_poa_middleware, layer=0)  # Inject POA middleware

    # Check if connected to Ethereum network
    if not web3.is_connected():
        raise Exception("Not connected to Ethereum network")

    # Set up the sender's account
    sender_account = Account.from_key(private_key)
    sender_address = sender_account.address

    # Transaction details
    """
    虽然整个过程中都是wei ether
    但是实际是马蹄链
    
    """
    value = web3.to_wei(0, 'ether')
    logger.info(f"value={value}")

    # 为什么是等待状态中？我看松鼠的也这么写的
    nonce = web3.eth.get_transaction_count(sender_address, 'pending')
    logger.info(f"nonce={nonce}")

    # Convert data to hex and add as data to the transaction
    data_hex = web3.to_hex(text=text_data)
    logger.info(f"data_hex={data_hex}")





    # Estimate gas limit for the transaction
    """
    gas居然还能估计
    这是gwei个数的估算
    复现一遍原理 gas_estimate *  （base_fee + max_priority_fee_per_gas ） 就是总费用
    """
    gas_estimate = web3.eth.estimate_gas({
        'to': recipient_address,
        'value': value,
        'from': sender_address,
        'data': data_hex
    })

    logger.info(f"gas_estimate={gas_estimate}")



    # 不要直接链上获取，自己填更快上链。直接默认更省心   要提高一点点？ 默认是 web3.eth.gas_price,
    if get_fee_realtime:
        # !! 这里灵活调整，现在是直接读链上默认值 ！！！！！！
        fee_wei = web3.eth.gas_price
    else:
        fee_wei = web3.to_wei(fee_input, 'gwei')  # 从https://bscscan.com/gastracker 里面看的

    logger.info(f"fee_wei={fee_wei}")








    # Create the transaction dictionary
    transaction = {

        # 通过我自己尝试，这个会根据rpc是什么自动改编，不需要操心
        'chainId': web3.eth.chain_id,  # 试了试去掉报错。但是我不是eth是，马蹄莲，这是这个id？

        'to': recipient_address,  # 去哪
        'from': recipient_address,  # 从哪来 #我看网上有人加了，我就加

        'nonce': nonce,

        'gas': gas_estimate,

        'gasPrice': fee_wei,

        'value': value,  # 金额是0
        'data': data_hex  # 数据是铭文格式
    }
    logger.info(f"Transaction: {transaction}")
    return transaction, web3, private_key, nonce


def signed_send(transaction, web3, private_key, is_wait=True):
    """
    基本原理就是先签名
    再send raw
    就算一次tx了
    """
    # Sign the transaction
    signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    # Get the transaction hash
    logger.info(f"Transaction hash: {tx_hash.hex()}")
    # Wait for the transaction receipt (optional)
    if is_wait:
        """
        就是一直等,等交易成功，默认超时时间120s
        """
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info(f"Transaction receipt: {tx_receipt}")
        logger.info(f"Transaction status: {tx_receipt['status']}")


def send_transaction(number, rpc, test_data, is_wait=True, fee_input=3, get_fee_realtime=True):
    transaction, web3, private_key, nonce = get_transaction_eip1559(rpc, test_data, fee_input, get_fee_realtime)
    for i in range(number):
        transaction.update({'nonce': nonce})
        signed_send(transaction, web3, private_key, is_wait)
        nonce = nonce + 1

    logger.info(f"end！！")

if __name__ == '__main__':
    send_transaction(1, rpc_map.get("mainnet"), data, is_wait=True, fee_input=3, get_fee_realtime=True)
