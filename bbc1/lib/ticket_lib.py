# -*- coding: utf-8 -*-
"""
Copyright (c) 2019 beyond-blockchain.org.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import msgpack
import sys
import time

sys.path.append("../../")

from bbc1.core import bbclib
from bbc1.core.libs import bbclib_utils
from bbc1.core import logger, bbc_app
from bbc1.core.bbc_error import *
from bbc1.core.message_key_types import KeyType
from bbc1.core.bbc_config import DEFAULT_CORE_PORT
from bbc1.lib import app_support_lib


NAME_OF_DB = 'ticket_db'

ticket_tx_id_table_definition = [
    ["tx_id", "BLOB"],
    ["tx", "BLOB"],
]

ticket_id_table_definition = [
    ["ticket_id", "BLOB"],
    ["ticket", "BLOB"],
]

ticket_table_definition = [
    ["service_id", "BLOB"],
    ["user_id", "BLOB"],
    ["tx_id", "BLOB"],
    ["event_idx", "INTEGER"],
    ["ticket_id", "BLOB"],
    ["is_single", "INTEGER"],
    ["state", "INTEGER"],
    ["last_modified", "INTEGER"]
]

IDX_BOOTH_ID      = 0
IDX_USER_ID       = 1
IDX_TX_ID         = 2
IDX_EVENT_IDX     = 3
IDX_TICKET_ID     = 4
IDX_IS_SINGLE     = 5
IDX_STATE         = 6
IDX_LAST_MODIFIED = 7

ST_FREE     = 0
ST_RESERVED = 1
ST_TAKEN    = 2


class Constants(app_support_lib.Constants):

    DESC_BINARY     = 0
    DESC_DICTIONARY = 1
    DESC_STRING     = 2

    O_BIT_DIVISIBLE     = 0b0000000000000001
    O_BIT_TRANSFERABLE  = 0b0000000000000010
    O_BIT_RELATIVE_TIME = 0b0000000000000100

    VERSION_CURRENT = 0


class TicketSpec:

    def __init__(self, dic=None, description=None, value=None, unit=None,
            book_of=1,
            time_to_begin=0, time_to_end=Constants.MAX_INT64, expire_after=0,
            option_divisible=False,
            option_transferable=True,
            option_relative_time=False,
            version=Constants.VERSION_CURRENT):
        self.version = version

        if dic is not None:
            description = dic['description']
        if isinstance(description, str):
            raw = description.encode()
        elif isinstance(description, dict):
            raw = msgpack.dumps(description, encoding='utf-8')
        else:
            raw = description
        if len(raw) > Constants.MAX_INT16:
            raise TypeError('description is too long')
        self.description = description

        if dic is not None:
            try:
                value = dic['value']
            except KeyError:
                value = 0
        if not isinstance(value, int):
            raise TypeError('value must be int')
        if value < -Constants.MAX_INT64 or value > Constants.MAX_INT64:
            raise TypeError('value out of range')
        self.value = value

        if dic is not None:
            try:
                unit = dic['unit']
            except KeyError:
                unit = ""
        if not isinstance(unit, str):
            raise TypeError('unit must be str')
        string = unit.encode()
        if len(string) > Constants.MAX_INT8:
            raise TypeError('unit is too long')
        self.unit = unit

        if dic is not None:
            try:
                book_of = dic['book_of']
            except KeyError:
                book_of = 1
        if not isinstance(book_of, int):
            raise TypeError('book_of must be int')
        if book_of <= 0 or book_of > Constants.MAX_INT16:
            raise TypeError('book_of out of range')
        self.book_of = book_of

        if dic is not None:
            try:
                time_to_begin = dic['time_to_begin']
            except KeyError:
                time_to_begin = 0
        if not isinstance(time_to_begin, int):
            raise TypeError('time_to_begin must be int')
        if time_to_begin < 0 or time_to_begin > Constants.MAX_INT64:
            raise TypeError('time_to_begin out of range')
        self.time_to_begin = time_to_begin

        if dic is not None:
            try:
                time_to_end = dic['time_to_end']
            except KeyError:
                time_to_end = Constants.MAX_INT64
        if not isinstance(time_to_end, int):
            raise TypeError('time_to_end must be int')
        if time_to_end <= 0 or time_to_end > Constants.MAX_INT64:
            raise TypeError('time_to_end out of range')
        self.time_to_end = time_to_end

        if dic is not None:
            try:
                expire_after = dic['expire_after']
            except KeyError:
                expire_after = 0
        if not isinstance(expire_after, int):
            raise TypeError('expire_after must be int')
        if expire_after < 0 or expire_after > Constants.MAX_INT64:
            raise TypeError('expire_after out of range')
        self.expire_after = expire_after

        if dic is not None:
            try:
                option_divisible = dic['option_divisible']
            except KeyError:
                option_divisible = False
        if not isinstance(option_divisible, bool):
            raise TypeError('this option must be bool')
        self.option_divisible = option_divisible

        if dic is not None:
            try:
                option_transferable = dic['option_transferable']
            except KeyError:
                option_tranferable = False
        if not isinstance(option_transferable, bool):
            raise TypeError('this option must be bool')
        self.option_transferable = option_transferable

        if dic is not None:
            try:
                option_relative_time = dic['option_relative_time']
            except KeyError:
                option_relative_time = False
        if not isinstance(option_relative_time, bool):
            raise TypeError('this option must be bool')
        self.option_relative_time = option_relative_time


    def __eq__(self, other):
        if isinstance(other, TicketSpec):
            if self.description != other.description \
                    or self.value != other.value \
                    or self.unit != other.unit \
                    or self.book_of != other.book_of \
                    or self.time_to_begin != other.time_to_begin \
                    or self.time_to_end != other.time_to_end \
                    or self.expire_after != other.expire_after \
                    or self.option_divisible != other.option_divisible \
                    or self.option_transferable != other.option_transferable \
                    or self.option_relative_time != other.option_relative_time:
                return False
            return True
        else:
            return False


    @staticmethod
    def from_serialized_data(ptr, data):
        try:
            ptr, version = bbclib_utils.get_n_byte_int(ptr, 2, data)
            ptr, t = bbclib_utils.get_n_byte_int(ptr, 1, data)
            ptr, size = bbclib_utils.get_n_byte_int(ptr, 2, data)
            ptr, v = bbclib_utils.get_n_bytes(ptr, size, data)
            if t == Constants.DESC_STRING:
                description = v.decode()
            elif t == Constants.DESC_DICTIONARY:
                description = msgpack.loads(v, encoding='utf-8')
            else:
                description = v
            ptr, size = bbclib_utils.get_n_byte_int(ptr, 1, data)
            ptr, v = bbclib_utils.get_n_bytes(ptr, size, data)
            unit = v.decode()
            ptr, value = bbclib_utils.get_n_byte_int(ptr, 8, data)
            ptr, book_of = bbclib_utils.get_n_byte_int(ptr, 2, data)
            ptr, time_to_begin = bbclib_utils.get_n_byte_int(ptr, 8, data)
            ptr, time_to_end = bbclib_utils.get_n_byte_int(ptr, 8, data)
            ptr, expire_after = bbclib_utils.get_n_byte_int(ptr, 8, data)
            ptr, v = bbclib_utils.get_n_byte_int(ptr, 2, data)
            option_divisible = v & Constants.O_BIT_DIVISIBLE != 0
            option_transferable = v & Constants.O_BIT_TRANSFERABLE != 0
            option_relative_time = v & Constants.O_BIT_RELATIVE_TIME != 0
        except:
            raise
        return ptr, TicketSpec(description=description, value=value, unit=unit,
                book_of=book_of,
                time_to_begin=time_to_begin, time_to_end=time_to_end,
                expire_after=expire_after,
                option_divisible=option_divisible,
                option_transferable=option_transferable,
                option_relative_time=option_relative_time,
                version=version)


    def serialize(self):
        dat = bytearray(bbclib_utils.to_2byte(self.version))
        if isinstance(self.description, str):
            dat.extend(bbclib_utils.to_1byte(Constants.DESC_STRING))
            string = self.description.encode()
            dat.extend(bbclib_utils.to_2byte(len(string)))
            dat.extend(string)
        elif isinstance(self.description, dict):
            dat.extend(bbclib_utils.to_1byte(Constants.DESC_DICTIONARY))
            raw = msgpack.dumps(self.description, encoding='utf-8')
            dat.extend(bbclib_utils.to_2byte(len(raw)))
            dat.extend(raw)
        else:
            dat.extend(bbclib_utils.to_1byte(Constants.DESC_BINARY))
            dat.extend(bbclib_utils.to_2byte(len(self.description)))
            dat.extend(self.description)
        string = self.unit.encode()
        dat.extend(bbclib_utils.to_1byte(len(string)))
        dat.extend(string)
        dat.extend(bbclib_utils.to_8byte(self.value))
        dat.extend(bbclib_utils.to_2byte(self.book_of))
        dat.extend(bbclib_utils.to_8byte(self.time_to_begin))
        dat.extend(bbclib_utils.to_8byte(self.time_to_end))
        dat.extend(bbclib_utils.to_8byte(self.expire_after))

        options = Constants.O_BIT_NONE
        if self.option_divisible:
            options |= Constants.O_BIT_DIVISIBLE
        if self.option_transferable:
            options |= Constants.O_BIT_TRANSFERABLE
        if self.option_relative_time:
            options |= Constants.O_BIT_RELATIVE_TIME
        dat.extend(bbclib_utils.to_2byte(options))
        return bytes(dat)


class Ticket:

    T_TICKET    = 0b0000
    T_TICKET_ID = 0b0001

    def __init__(self, ticket_id=None, spec=None, time_of_origin=None):
        self.ticket_id = ticket_id
        self.spec = spec
        self.time_of_origin = time_of_origin


    @staticmethod
    def from_serialized_data(ptr, data):
        try:
            ptr, type = bbclib_utils.get_n_byte_int(ptr, 1, data)
            if type == Ticket.T_TICKET:
                ticket_id = None
                ptr, spec = TicketSpec.from_serialized_data(ptr, data)
                ptr, time_of_origin = bbclib_utils.get_n_byte_int(ptr, 8, data)
            elif type == Ticket.T_TICKET_ID:
                ptr, ticket_id = bbclib_utils.get_bigint(ptr, data)
                spec = None
                time_of_origin = None
        except:
            raise

        obj = Ticket(ticket_id, spec, time_of_origin)
        return ptr, obj


    def is_divisible(self):
        return self.spec.option_divisible


    def is_relative_time(self):
        return self.spec.option_relative_time


    def is_transferable(self):
        return self.spec.option_transferable


    def redeem(self):
        pass


    def serialize(self):
        if self.ticket_id is None:
            dat = bytearray(bbclib_utils.to_1byte(Ticket.T_TICKET))
            dat.extend(self.spec.serialize())
            dat.extend(bbclib_utils.to_8byte(self.time_of_origin))
        else:
            dat = bytearray(bbclib_utils.to_1byte(Ticket.T_TICKET_ID))
            dat.extend(bbclib_utils.to_bigint(self.ticket_id))
        return bytes(dat)


    def split(self):
        pass


class Store:

    def __init__(self, domain_id, service_id, app):
        self.domain_id = domain_id
        self.service_id = service_id
        self.app = app
        self.db_online = True
        self.db = app_support_lib.Database()
        self.db.setup_db(domain_id, NAME_OF_DB)
        self.db.create_table_in_db(domain_id, NAME_OF_DB,
                'ticket_table',
                ticket_table_definition,
                indices=[0, 1, 2, 4])
        self.db.create_table_in_db(domain_id, NAME_OF_DB,
                'ticket_tx_id_table',
                ticket_tx_id_table_definition,
                primary_key=0, indices=[1])
        self.db.create_table_in_db(domain_id, NAME_OF_DB,
                'ticket_id_table',
                ticket_id_table_definition,
                primary_key=0, indices=[1])
        self.independent = False


    def delete_utxo(self, tx_id, idx):
        if self.db_online is False:
            return None
        return self.db.exec_sql(
            self.domain_id,
            NAME_OF_DB,
            ('update ticket_table set state=?, last_modified=? where '
             'tx_id=? and event_idx=?'),
            ST_TAKEN,
            int(time.time()),
            tx_id,
            idx
        )


    def get_balance_of(self, user_id, eval_time=None):
        rows = self.read_utxo_list(user_id)
        if len(rows) == 0:
            return 0

        if eval_time is None:
            eval_time = int(time.time())
        
        balance = 0
        for row in rows:
            ticket_id = row[IDX_TICKET_ID]
            ticket = self.get_ticket(ticket_id)
            balance += ticket.spec.value
        return balance
      

    def get_ticket(self, ticket_id):
        if self.db_online is False:
            return None
        rows = self.db.exec_sql(
            self.domain_id,
            NAME_OF_DB,
            'select ticket from ticket_id_table where ticket_id=?',
            ticket_id
        )
        if len(rows) <= 0:
            return None
        _, ticket = Ticket.from_serialized_data(0, rows[0][0])
        return ticket


    def get_tx(self, tx_id):
        self.app.search_transaction(tx_id)
        res = self.app.callback.synchronize()
        if res[KeyType.status] < ESUCCESS:
            raise ValueError('not found')
        tx, fmt = bbclib.deserialize(res[KeyType.transaction_data])
        return tx


    def get_usable_event(self, user_id, ticket_id):
        rows = self.read_utxo(user_id, ticket_id)
        if len(rows) <= 0:
            raise
        tx_id = rows[0][IDX_TX_ID]
        index = rows[0][IDX_EVENT_IDX]
        return self.get_tx(tx_id), index


    def insert(self, tx, user_id, idPublickeyMap):
        if idPublickeyMap.verify_signers(tx, self.service_id,
                user_id) == False:
            raise RuntimeError('signers not verified')

        self.push_tx(tx.transaction_id, tx)
        ret = self.app.insert_transaction(tx)
        assert ret
        res = self.app.callback.synchronize()
        if res[KeyType.status] < ESUCCESS:
            raise RuntimeError(res[KeyType.reason].decode())


    def inserted(self, tx_id):
        tx = self.take_tx(tx_id)
        if tx is None:
            return

        # FIXME: check validity
        for i, event in enumerate(tx.events):
            if event.asset_group_id == self.service_id:
                _, ticket = Ticket.from_serialized_data(0,
                        event.asset.asset_body)
                if ticket.ticket_id is None:
                    ticket.ticket_id = event.asset.asset_id
                    self.put_ticket(ticket.ticket_id, event.asset.asset_body)
                self.write_utxo(event.asset.user_id,
                        tx.transaction_id, i, ticket.ticket_id, True)

        for ref in tx.references:
            if ref.asset_group_id == self.service_id:
                self.delete_utxo(ref.transaction_id, ref.event_index_in_ref)


    def is_valid_holder(self, user_id, ticket_id, eval_time=None):
        rows = self.read_utxo(user_id, ticket_id)
        return len(rows) > 0


    def push_tx(self, tx_id, tx):
        if self.db_online is False:
            return
        self.db.exec_sql(
            self.domain_id,
            NAME_OF_DB,
            'insert into ticket_tx_id_table values (?, ?)',
            tx_id,
            bbclib.serialize(tx)
        )


    def put_ticket(self, ticket_id, ticket):
        if self.db_online is False:
            return
        self.db.exec_sql(
            self.domain_id,
            NAME_OF_DB,
            'insert into ticket_id_table values (?, ?)',
            ticket_id,
            ticket
        )


    def read_utxo(self, user_id, ticket_id):
        return self.db.exec_sql(
            self.domain_id,
            NAME_OF_DB,
            ('select * from ticket_table where '
             'service_id=? and user_id=? and ticket_id=? and state=?'),
            self.service_id,
            user_id,
            ticket_id,
            ST_FREE
        )


    def read_utxo_list(self, user_id):
        return self.db.exec_sql(
            self.domain_id,
            NAME_OF_DB,
            ('select * from ticket_table where '
             'service_id=? and user_id=? and state=?'),
            self.service_id,
            user_id,
            ST_FREE
        )


    def reserve_utxo(self, tx_id, idx):
        if self.db_online is False:
            return None
        return self.db.exec_sql(
            self.domain_id,
            NAME_OF_DB,
            ('update ticket_table set state=?, last_modified=? where '
             'tx_id=? and event_idx=?'),
            ST_RESERVED,
            int(time.time()),
            tx_id,
            idx
        )


    def reserve_referred_utxos(self, tx):
        for ref in tx.references:
            if ref.asset_group_id == self.service_id:
                self.reserve_utxo(ref.transaction_id, ref.event_index_in_ref)

    '''
    mainly for testing purposes.
    '''
    def set_db_online(self, is_online=True):
        self.db_online = is_online


    def sign(self, transaction, user_id, keypair):
        sig = transaction.sign(
                private_key=keypair.private_key,
                public_key=keypair.public_key)
        transaction.add_signature(user_id=user_id, signature=sig)
        return sig


    def sign_and_insert(self, transaction, user_id, keypair, idPublickeyMap):
        self.sign(transaction, user_id, keypair)
        transaction.digest()
        self.insert(transaction, user_id, idPublickeyMap)
        return transaction


    def take_tx(self, tx_id):
        if self.db_online is False:
            return None
        rows = self.db.exec_sql(
            self.domain_id,
            NAME_OF_DB,
            'select tx from ticket_tx_id_table where tx_id=?',
            tx_id
        )
        if len(rows) <= 0:
            return None
        tx, fmt = bbclib.deserialize(rows[0][0])
        if self.independent:
            self.db.exec_sql(
                self.domain_id,
                NAME_OF_DB,
                'delete from ticket_tx_id_table where tx_id=?',
                tx_id
            )
        return tx


    def write_utxo(self, user_id, tx_id, idx, ticket_id, is_single):
        if self.db_online is False:
            return
        self.db.exec_sql(
            self.domain_id,
            NAME_OF_DB,
            'insert into ticket_table values (?, ?, ?, ?, ?, ?, ?, ?)',
            self.service_id,
            user_id,
            tx_id,
            idx,
            ticket_id,
            is_single,
            ST_FREE,
            int(time.time())
        )


class BBcTicketService:

    def __init__(self, domain_id, service_id, user_id, idPublickeyMap,
            port=DEFAULT_CORE_PORT, logname="-", loglevel="none"):
        self.logger = logger.get_logger(key="ticket_lib", level=loglevel,
                                        logname=logname) # FIXME: use logger
        self.domain_id = domain_id
        self.service_id = service_id
        self.user_id = user_id
        self.idPublickeyMap = idPublickeyMap
        self.app = bbc_app.BBcAppClient(port=DEFAULT_CORE_PORT,
                multiq=False, loglevel=loglevel)
        self.app.set_user_id(user_id)
        self.app.set_domain_id(domain_id)
        self.app.set_callback(ServiceCallback(logger, self))
        ret = self.app.register_to_core()
        assert ret

        self.store = Store(self.domain_id, self.service_id, self.app)
        self.app.request_insert_completion_notification(self.service_id)


    def get_balance_of(self, user_id, eval_time=None):
        if eval_time is None:
            eval_time = int(time.time())
        return self.store.get_balance_of(user_id, eval_time)


    def get_total_supply(self, time):
        pass


    def is_valid(self, ticket_id, eval_time=None):
        pass


    def is_valid_holder(self, user_id, ticket_id, eval_time=None):
        return self.store.is_valid_holder(user_id, ticket_id, eval_time)


    def issue(self, to_user_id, spec, time_of_origin=None, keypair=None):
        if self.user_id != self.service_id:
            raise RuntimeError('issuer must be the ticket service')

        tx = bbclib.make_transaction(event_num=1)
        tx.events[0].asset_group_id = self.service_id
        if time_of_origin is None:
            time_of_origin = tx.timestamp
        tx.events[0].asset.add(user_id=to_user_id,
                asset_body=Ticket(
                spec=spec, time_of_origin=time_of_origin).serialize())
        ticket_id = tx.events[0].asset.asset_id
        # FIXME: check collision of ticket_id

        tx.events[0].add(mandatory_approver=self.service_id)
        tx.events[0].add(mandatory_approver=to_user_id)
        tx.add(witness=bbclib.BBcWitness())
        tx.witness.add_witness(self.service_id)

        if keypair is None:
            return ticket_id, tx

        return ticket_id, self.store.sign_and_insert(tx, self.service_id,
                keypair, self.idPublickeyMap)


    def make_event(self, ref_indices, user_id, ticket):
        event = bbclib.BBcEvent(asset_group_id=self.service_id)
        for i in ref_indices:
            event.add(reference_index=i)
        event.add(mandatory_approver=self.service_id)
        event.add(mandatory_approver=user_id)
        event.add(asset=bbclib.BBcAsset())
        event.asset.add(user_id=user_id, asset_body=ticket.serialize())
        return event


    def redeem(self, from_user_id, ticket_id, transaction=None,
            keypair_from=None, keypair_service=None):
        tx = self.transfer(from_user_id, self.service_id, ticket_id,
                transaction, keypair_from, keypair_service)
        return tx


    def set_keypair(self, keypair):
       self.app.callback.set_keypair(keypair)


    def sign_and_insert(self, transaction, user_id, keypair):
        return self.store.sign_and_insert(transaction, user_id, keypair,
                self.idPublickeyMap)


    def split(self, ticket_id):
        pass


    def swap(self, ticket_id):
        pass


    def transfer(self, from_user_id, to_user_id, ticket_id, transaction=None,
            keypair_from=None, keypair_service=None):

        ticket = self.store.get_ticket(ticket_id)
        if ticket is None:
            raise TypeError('ticket does not exist')
        if not ticket.is_transferable():
            raise TypeError('ticket is not transferable')

        if transaction is None:
            tx = bbclib.BBcTransaction()
            base_refs = 0
        else:
            tx = transaction
            base_refs = len(tx.references)

        ref_tx, index = self.store.get_usable_event(from_user_id, ticket_id)

        ref = bbclib.BBcReference(asset_group_id=self.service_id,
                transaction=tx, ref_transaction=ref_tx,
                event_index_in_ref=index)
        tx.add(reference=ref)
        ticket = Ticket(ticket_id=ticket_id)
        tx.add(event=self.make_event([base_refs], to_user_id, ticket))

        if keypair_from is None:
            return tx

        if keypair_service is None:
            self.app.gather_signatures(tx, destinations=[self.service_id])
            res = self.app.callback.synchronize()
            if res[KeyType.status] < ESUCCESS:
                raise RuntimeError(res[KeyType.reason].decode())
            result = res[KeyType.result]
            tx.add_signature(self.service_id, signature=result[2])
            return self.store.sign_and_insert(tx, from_user_id, keypair_from,
                    self.idPublickeyMap)

        self.store.sign(tx, from_user_id, keypair_from)

        return self.store.sign_and_insert(tx, self.service_id, keypair_service,
                self.idPublickeyMap)


class ServiceCallback(bbc_app.Callback):

    def __init__(self, logger, service):
        super().__init__(logger)
        self.service = service
        self.keypair = None


    def proc_cmd_sign_request(self, dat):
        source_user_id = dat[KeyType.source_user_id]

        if self.keypair is None:
            self.service.app.sendback_denial_of_sign(source_user_id,
                    'keypair is unset')

        tx, fmt = bbclib.deserialize(dat[KeyType.transaction_data])

        # FIXME: check validity

        sig = self.service.store.sign(tx, self.service.user_id, self.keypair)
        tx.digest()

        self.service.store.reserve_referred_utxos(tx)
        self.service.store.push_tx(tx.transaction_id, tx)
        self.service.app.sendback_signature(source_user_id, tx.transaction_id,
                -1, sig)


    def proc_notify_inserted(self, dat):
        self.service.store.inserted(dat[KeyType.transaction_id])


    def set_keypair(self, keypair):
        self.keypair = keypair


# end of ticket_lib.py
