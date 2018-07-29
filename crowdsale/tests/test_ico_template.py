from boa_test.tests.boa_test import BoaFixtureTest
from boa.compiler import Compiler
from neo.Core.TX.Transaction import Transaction
from neo.Prompt.Commands.BuildNRun import TestBuild
from neo.EventHub import events
from neo.SmartContract.SmartContractEvent import SmartContractEvent, NotifyEvent
from neo.Settings import settings
from neo.Prompt.Utils import parse_param
from neo.Core.FunctionCode import FunctionCode
from neocore.Fixed8 import Fixed8
# from boa_test.example.demo.nex.token import *
from senno.token import *

import shutil
import os
import time

settings.USE_DEBUG_STORAGE = True
settings.DEBUG_STORAGE_PATH = './fixtures/debugstorage'


class TestContract(BoaFixtureTest):

    dispatched_events = []
    dispatched_logs = []

    @classmethod
    def tearDownClass(cls):
        super(BoaFixtureTest, cls).tearDownClass()

        try:
            if os.path.exists(settings.DEBUG_STORAGE_PATH):
                shutil.rmtree(settings.DEBUG_STORAGE_PATH)
        except Exception as e:
            print("couldn't remove debug storage %s " % e)

    @classmethod
    def setUpClass(cls):
        super(TestContract, cls).setUpClass()

        cls.dirname = '/'.join(os.path.abspath(__file__).split('/')[:-2])

        def on_notif(evt):
            print(evt)
            cls.dispatched_events.append(evt)
            print("dispatched events %s " % cls.dispatched_events)

        def on_log(evt):
            print(evt)
            cls.dispatched_logs.append(evt)
        events.on(SmartContractEvent.RUNTIME_NOTIFY, on_notif)
        events.on(SmartContractEvent.RUNTIME_LOG, on_log)

    def test_ICOTemplate_1(self):

        output = Compiler.instance().load('%s/ico_template.py' % TestContract.dirname).default
        out = output.write()
#        print(output.to_s())

        tx, results, total_ops, engine = TestBuild(out, ['name', '[]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetString(), TOKEN_NAME)

        tx, results, total_ops, engine = TestBuild(out, ['symbol', '[]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetString(), TOKEN_SYMBOL)

        tx, results, total_ops, engine = TestBuild(out, ['decimals', '[]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), TOKEN_DECIMALS)

        tx, results, total_ops, engine = TestBuild(out, ['totalSupply', '[]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 0)

        tx, results, total_ops, engine = TestBuild(out, ['nonexistentmethod', '[]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetString(), 'unknown operation')

        # deploy with wallet 2 should fail CheckWitness
        tx, results, total_ops, engine = TestBuild(out, ['deploy', '[]'], self.GetWallet2(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        tx, results, total_ops, engine = TestBuild(out, ['deploy', '[]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)

        # second time, it should already be deployed and return false
        tx, results, total_ops, engine = TestBuild(out, ['deploy', '[]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        # now total supply should be equal to the initial owner amount
        tx, results, total_ops, engine = TestBuild(out, ['totalSupply', '[]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), TOKEN_INITIAL_AMOUNT)

        # now the owner should have a balance of the TOKEN_INITIAL_AMOUNT
        tx, results, total_ops, engine = TestBuild(out, ['balanceOf', parse_param([bytearray(TOKEN_OWNER)])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), TOKEN_INITIAL_AMOUNT)


    def test_ICOTemplate_1_start(self):
        output = Compiler.instance().load('%s/ico_template.py' % TestContract.dirname).default
        out = output.write()

        # crowsale not start
        tx, results, total_ops, engine = TestBuild(out, ['has_started', '[]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        # start crowsale should fail CheckWitness
        tx, results, total_ops, engine = TestBuild(out, ['start_crowdsale', '[1510240782]'], self.GetWallet2(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        # get crowdsale time return false since not yet start
        tx, results, total_ops, engine = TestBuild(out, ['crowdsale_time', '[]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        # start crowdsale
        tx, results, total_ops, engine = TestBuild(out, ['start_crowdsale', '[1510240782]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 1510240782)

        # crowdsale shall not started because block timestamp less than 1510240782
        tx, results, total_ops, engine = TestBuild(out, ['has_started', '[]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        # start crowdsale at time earlier than latest block timestamp
        tx, results, total_ops, engine = TestBuild(out, ['start_crowdsale', '[1510240700]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 1510240700)

        # get crowdsale time return timestamp
        tx, results, total_ops, engine = TestBuild(out, ['crowdsale_time', '[]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 1510240700)

        # crowdsale shall return started
        tx, results, total_ops, engine = TestBuild(out, ['has_started', '[]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)

    def test_ICOTemplate_2(self):

        output = Compiler.instance().load('%s/ico_template.py' % TestContract.dirname).default
        out = output.write()

        # now transfer tokens to wallet 2

        TestContract.dispatched_events = []

        test_transfer_amount = 2400000001
        tx, results, total_ops, engine = TestBuild(out, ['transfer', parse_param([bytearray(TOKEN_OWNER), self.wallet_2_script_hash.Data, test_transfer_amount])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)

        self.assertEqual(len(TestContract.dispatched_events), 1)
        evt = TestContract.dispatched_events[0]
        self.assertIsInstance(evt, NotifyEvent)
        self.assertEqual(evt.addr_from.Data, bytearray(TOKEN_OWNER))
        self.assertEqual(evt.addr_to, self.wallet_2_script_hash)
        self.assertEqual(evt.amount, test_transfer_amount)

        # now get balance of wallet 2
        tx, results, total_ops, engine = TestBuild(out, ['balanceOf', parse_param([self.wallet_2_script_hash.Data])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), test_transfer_amount)

        # now the owner should have less
        tx, results, total_ops, engine = TestBuild(out, ['balanceOf', parse_param([bytearray(TOKEN_OWNER)])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), TOKEN_INITIAL_AMOUNT - test_transfer_amount)

        # now this transfer should fail
        tx, results, total_ops, engine = TestBuild(out, ['transfer', parse_param([bytearray(TOKEN_OWNER), self.wallet_2_script_hash.Data, TOKEN_INITIAL_AMOUNT])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        # this transfer should fail because it is not signed by the 'from' address
        tx, results, total_ops, engine = TestBuild(out, ['transfer', parse_param([bytearray(TOKEN_OWNER), self.wallet_2_script_hash.Data, 10000])], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        # now this transfer should fail, this is from address with no tokens
        tx, results, total_ops, engine = TestBuild(out, ['transfer', parse_param([self.wallet_3_script_hash.Data, self.wallet_2_script_hash.Data, 1000])], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        # get balance of bad data
        tx, results, total_ops, engine = TestBuild(out, ['balanceOf', parse_param(['abc'])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 0)

        # get balance no params
        tx, results, total_ops, engine = TestBuild(out, ['balanceOf', parse_param([])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

    def test_ICOTemplate_3_KYC(self):

        output = Compiler.instance().load('%s/ico_template.py' % TestContract.dirname).default
        out = output.write()
        print(output.to_s())
        # now transfer tokens to wallet 2

        TestContract.dispatched_events = []

        # test mint tokens without being kyc verified
        tx, results, total_ops, engine = TestBuild(out, ['mintTokens', '[]', '--attach-neo=10'], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        # Try to register as a non owner
        tx, results, total_ops, engine = TestBuild(out, ['crowdsale_register', parse_param([self.wallet_3_script_hash.Data])], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        # Get status of non registered address
        tx, results, total_ops, engine = TestBuild(out, ['crowdsale_status', parse_param([self.wallet_3_script_hash.Data])], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        TestContract.dispatched_events = []

        # register an address
        tx, results, total_ops, engine = TestBuild(out, ['crowdsale_register', parse_param([self.wallet_3_script_hash.Data])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 1)

        # it should dispatch an event
        self.assertEqual(len(TestContract.dispatched_events), 1)
        evt = TestContract.dispatched_events[0]
        # self.assertEqual(evt.event_payload[0], b'kyc_registration')

        # register 2 addresses at once
        tx, results, total_ops, engine = TestBuild(out, ['crowdsale_register', parse_param([self.wallet_3_script_hash.Data, self.wallet_2_script_hash.Data])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 2)

        # now check reg status
        tx, results, total_ops, engine = TestBuild(out, ['crowdsale_status', parse_param([self.wallet_3_script_hash.Data])], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)

    def test_ICOTemplate_4_attachments(self):

        output = Compiler.instance().load('%s/ico_template.py' % TestContract.dirname).default
        out = output.write()

        # test mint tokens without being kyc verified
        tx, results, total_ops, engine = TestBuild(out, ['get_attachments', '[]', '--attach-neo=10'], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        attachments = results[0].GetArray()
        self.assertEqual(len(attachments), 4)

        fn = FunctionCode(out, '0705', '05')

        self.assertEqual(attachments[0].GetByteArray(), fn.ScriptHash().Data)
        self.assertEqual(attachments[1].GetByteArray(), self.wallet_3_script_hash.Data)
        self.assertEqual(attachments[2].GetBigInteger(), Fixed8.FromDecimal(10).value)
        self.assertEqual(attachments[3].GetBigInteger(), 0)

        tx, results, total_ops, engine = TestBuild(out, ['get_attachments', '[]'], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        attachments = results[0].GetArray()
        self.assertEqual(len(attachments), 4)

        self.assertEqual(attachments[1].GetByteArray(), bytearray())
        self.assertEqual(attachments[2].GetBigInteger(), 0)
        self.assertEqual(attachments[3].GetBigInteger(), 0)

        tx, results, total_ops, engine = TestBuild(out, ['get_attachments', '[]', '--attach-neo=3', '--attach-gas=3.12'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        attachments = results[0].GetArray()
        self.assertEqual(len(attachments), 4)
        self.assertEqual(attachments[1].GetByteArray(), self.wallet_1_script_hash.Data)
        self.assertEqual(attachments[2].GetBigInteger(), Fixed8.FromDecimal(3).value)
        self.assertEqual(attachments[3].GetBigInteger(), Fixed8.FromDecimal(3.12).value)

    def test_ICOTemplate_5_mint(self):

        output = Compiler.instance().load('%s/ico_template.py' % TestContract.dirname).default
        out = output.write()

        # register an address
        tx, results, total_ops, engine = TestBuild(out, ['crowdsale_register', parse_param([self.wallet_3_script_hash.Data])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 1)

        TestContract.dispatched_events = []

        # test mint tokens, this should return true
        tx, results, total_ops, engine = TestBuild(out, ['mintTokens', '[]', '--attach-neo=10'], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)

        # it should dispatch an event
        self.assertEqual(len(TestContract.dispatched_events), 1)
        evt = TestContract.dispatched_events[0]
        self.assertIsInstance(evt, NotifyEvent)
        self.assertEqual(evt.amount, 10 * TOKENS_PER_NEO * 120 / 100)
        self.assertEqual(evt.addr_to, self.wallet_3_script_hash)

        # now the minter should have a balance
        tx, results, total_ops, engine = TestBuild(out, ['balanceOf', parse_param([self.wallet_3_script_hash.Data])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 10 * TOKENS_PER_NEO * 120 / 100)

        # test if the bonus is correct
        ## 10%: 1510240700 - 48*60*60
        tx, results, total_ops, engine = TestBuild(out, ['start_crowdsale', '[1510067800]'], self.GetWallet1(), '0705', '05')
        tx, results, total_ops, engine = TestBuild(out, ['mintTokens', '[]', '--attach-neo=10'], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)
        tx, results, total_ops, engine = TestBuild(out, ['balanceOf', parse_param([self.wallet_3_script_hash.Data])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 10 * TOKENS_PER_NEO * 120 / 100 + 10 * TOKENS_PER_NEO * 110 / 100)

        ## 7%: 1510240700 - 604800
        tx, results, total_ops, engine = TestBuild(out, ['start_crowdsale', '[1509635800]'], self.GetWallet1(), '0705', '05')
        tx, results, total_ops, engine = TestBuild(out, ['mintTokens', '[]', '--attach-neo=10'], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)
        tx, results, total_ops, engine = TestBuild(out, ['balanceOf', parse_param([self.wallet_3_script_hash.Data])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 10 * TOKENS_PER_NEO * 120 / 100 + 10 * TOKENS_PER_NEO * 110 / 100 + 10 * TOKENS_PER_NEO * 107 / 100)

        ## 3%: 1510240700 - 1209600
        tx, results, total_ops, engine = TestBuild(out, ['start_crowdsale', '[1509031000]'], self.GetWallet1(), '0705', '05')
        tx, results, total_ops, engine = TestBuild(out, ['mintTokens', '[]', '--attach-neo=10'], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)
        tx, results, total_ops, engine = TestBuild(out, ['balanceOf', parse_param([self.wallet_3_script_hash.Data])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 10 * TOKENS_PER_NEO * 120 / 100 + 10 * TOKENS_PER_NEO * 110 / 100 + 10 * TOKENS_PER_NEO * 107 / 100 + 10 * TOKENS_PER_NEO * 103 / 100)

        ## no bonus 
        tx, results, total_ops, engine = TestBuild(out, ['start_crowdsale', '[1508426200]'], self.GetWallet1(), '0705', '05')
        tx, results, total_ops, engine = TestBuild(out, ['mintTokens', '[]', '--attach-neo=10'], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)
        tx, results, total_ops, engine = TestBuild(out, ['balanceOf', parse_param([self.wallet_3_script_hash.Data])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 10 * TOKENS_PER_NEO * 120 / 100 + 10 * TOKENS_PER_NEO * 110 / 100 + 10 * TOKENS_PER_NEO * 107 / 100 + 10 * TOKENS_PER_NEO * 103 / 100 + 10 * TOKENS_PER_NEO)


        # now the total circulation should be bigger
        tx, results, total_ops, engine = TestBuild(out, ['totalSupply', '[]'], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 54000000000000 + TOKEN_INITIAL_AMOUNT)

    def test_ICOTemplate_6_approval(self):

        output = Compiler.instance().load('%s/ico_template.py' % TestContract.dirname).default
        out = output.write()

        # tranfer_from, approve, allowance
        tx, results, total_ops, engine = TestBuild(out, ['allowance', parse_param([self.wallet_3_script_hash.Data, self.wallet_2_script_hash.Data])], self.GetWallet2(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 0)

        # try to transfer from
        tx, results, total_ops, engine = TestBuild(out, ['transferFrom', parse_param([self.wallet_3_script_hash.Data, self.wallet_2_script_hash.Data, 10000])], self.GetWallet2(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        # try to approve from someone not yourself
        tx, results, total_ops, engine = TestBuild(out, ['approve', parse_param([self.wallet_3_script_hash.Data, self.wallet_2_script_hash.Data, 10000])], self.GetWallet2(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 0)

        # try to approve more than you have
        tx, results, total_ops, engine = TestBuild(out, ['approve', parse_param([self.wallet_3_script_hash.Data, self.wallet_2_script_hash.Data, TOKEN_INITIAL_AMOUNT])], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 0)

        TestContract.dispatched_events = []

        # approve should work
        tx, results, total_ops, engine = TestBuild(out, ['approve', parse_param([self.wallet_3_script_hash.Data, self.wallet_2_script_hash.Data, 1234])], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)

        # it should dispatch an event
        self.assertEqual(len(TestContract.dispatched_events), 1)
        evt = TestContract.dispatched_events[0]
        self.assertIsInstance(evt, NotifyEvent)
        self.assertEqual(evt.notify_type, b'approve')
        self.assertEqual(evt.amount, 1234)

        # check allowance
        tx, results, total_ops, engine = TestBuild(out, ['allowance', parse_param([self.wallet_3_script_hash.Data, self.wallet_2_script_hash.Data])], self.GetWallet2(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 1234)

        # approve should not be additive, it should overwrite previous approvals
        tx, results, total_ops, engine = TestBuild(out, ['approve', parse_param([self.wallet_3_script_hash.Data, self.wallet_2_script_hash.Data, 133234])], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)

        tx, results, total_ops, engine = TestBuild(out, ['allowance', parse_param([self.wallet_3_script_hash.Data, self.wallet_2_script_hash.Data])], self.GetWallet2(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 133234)

        # now you can transfer from
        tx, results, total_ops, engine = TestBuild(out, ['transferFrom', parse_param([self.wallet_3_script_hash.Data, self.wallet_2_script_hash.Data, 10000])], self.GetWallet2(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)

        # now the recevier should have a balance
        # it is equal to 10000 plus test_transfer_amount = 2400000001

        tx, results, total_ops, engine = TestBuild(out, ['balanceOf', parse_param([self.wallet_2_script_hash.Data])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 10000 + 2400000001)

        # now the allowance should be less
        tx, results, total_ops, engine = TestBuild(out, ['allowance', parse_param([self.wallet_3_script_hash.Data, self.wallet_2_script_hash.Data])], self.GetWallet2(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 133234 - 10000)

        # try to transfer too much, even with approval
        tx, results, total_ops, engine = TestBuild(out, ['transferFrom', parse_param([self.wallet_3_script_hash.Data, self.wallet_2_script_hash.Data, 14440000])], self.GetWallet2(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        # cant approve negative amounts
        tx, results, total_ops, engine = TestBuild(out, ['approve', parse_param([self.wallet_3_script_hash.Data, self.wallet_2_script_hash.Data, -1000])], self.GetWallet3(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

    def test_ICOTemplate_7_burn(self):
        output = Compiler.instance().load('%s/ico_template.py' % TestContract.dirname).default
        out = output.write()

        # burn tokens
        burn_amt = 1000000000 * 100000000
        tx, results, total_ops, engine = TestBuild(out, ['burn', '[%s]' % burn_amt ], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)

        # tokens burned
        tx, results, total_ops, engine = TestBuild(out, ['tokens_burned', '[]'], self.GetWallet2(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), burn_amt)

        # tokens available for sale
        tx, results, total_ops, engine = TestBuild(out, ['crowdsale_available', '[]'], self.GetWallet2(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 4000000000 * 100000000 - 54000000000000 - burn_amt)

        # burned is not counted in totalSupply
        tx, results, total_ops, engine = TestBuild(out, ['circulation', '[]'], self.GetWallet1(), '0705', '05')
        in_circ = results[0].GetBigInteger()
        tx, results, total_ops, engine = TestBuild(out, ['totalSupply', '[]'], self.GetWallet1(), '0705', '05')
        total_supply = results[0].GetBigInteger()
        self.assertEqual(in_circ, total_supply + burn_amt)

    def test_ICOTemplate_7_reserve(self):
        output = Compiler.instance().load('%s/ico_template.py' % TestContract.dirname).default
        out = output.write()

        burn_amt = 1000000000 * 100000000
        reserve_amt = burn_amt * 2
        reserve_amt_too_many = burn_amt * 4
        
        tx, results, total_ops, engine = TestBuild(out, ['balanceOf', parse_param([self.wallet_1_script_hash.Data])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 599999997599999999)

        # reserve for private sale fails CheckWitness
        tx, results, total_ops, engine = TestBuild(out, ['reserve_private', '[%s]' % reserve_amt], self.GetWallet2(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        # cannot reserve too many
        tx, results, total_ops, engine = TestBuild(out, ['reserve_private', '[%s]' % reserve_amt_too_many], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)

        # reserve success
        tx, results, total_ops, engine = TestBuild(out, ['reserve_private', '[%s]' % reserve_amt], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), True)

        tx, results, total_ops, engine = TestBuild(out, ['balanceOf', parse_param([self.wallet_1_script_hash.Data])], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 599999997599999999 + reserve_amt)

        # tokens available for sale
        tx, results, total_ops, engine = TestBuild(out, ['crowdsale_available', '[]'], self.GetWallet2(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBigInteger(), 4000000000 * 100000000 - 54000000000000 - burn_amt - reserve_amt)

        # cannot reserve twice
        tx, results, total_ops, engine = TestBuild(out, ['reserve_private', '[%s]' % 10000], self.GetWallet1(), '0705', '05')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].GetBoolean(), False)


