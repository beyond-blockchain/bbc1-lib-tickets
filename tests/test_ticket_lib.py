# -*- coding: utf-8 -*-
import hashlib
import sys
import time

sys.path.extend(["../"])

from bbc1.core import bbc_app
from bbc1.core import bbclib
from bbc1.core.bbc_config import DEFAULT_CORE_PORT
from bbc1.lib import id_lib, ticket_lib

domain_id = None
service_id = None
service_id_counter = None
idPubkeyMap = None
keypairs = None
keypairs_counter = None


def setup():
    global domain_id
    global service_id
    global service_id_counter
    global idPubkeyMap
    global keypairs
    global keypairs_counter

    domain_id = bbclib.get_new_id("test_ticket_lib", include_timestamp=False)

    tmpclient = bbc_app.BBcAppClient(port=DEFAULT_CORE_PORT, multiq=False,
            loglevel="all")
    tmpclient.domain_setup(domain_id)
    tmpclient.callback.synchronize()
    tmpclient.unregister_from_core()

    idPubkeyMap = id_lib.BBcIdPublickeyMap(domain_id)
    service_id, keypairs = idPubkeyMap.create_user_id(num_pubkeys=1)
    service_id_counter, keypairs_counter = idPubkeyMap.create_user_id(
            num_pubkeys=1)


def test_ticket_spec():

#   description can be any string representation of a ticket, such as,
#   "SpecialExpress/Ticket:Nozomi 323:ShinYokohama:Kyoto:Car 9:Seat 13A"
#   "Denki Groove 30th Anniversary Ultra Tour:Zepp Tokyo:S3-16:Open 1552640400"

    description = "Yokohama Municipal Subway Off-Peak Multiple"
    value = 270
    unit = "yen"
    book_of = 12
    time_to_begin = 60 * 60
    time_to_end = 60 * 60 * 24 * 365
    expire_after = 60 * 60 * 24 * 90

    ticket_spec_dict = {
        'description': description,
        'value': value,
        'unit': unit,
        'book_of': book_of,
        'time_to_begin': time_to_begin,
        'time_to_end': time_to_end,
        'expire_after': expire_after,
        'option_divisible': True,
        'option_transferable': False,
        'option_relative_time': True,
    }

    spec = ticket_lib.TicketSpec(ticket_spec_dict)

    assert spec.description == description
    assert spec.value == value
    assert spec.unit == unit
    assert spec.book_of == book_of
    assert spec.time_to_begin == time_to_begin
    assert spec.time_to_end == time_to_end
    assert spec.expire_after == expire_after
    assert spec.option_divisible == True
    assert spec.option_transferable == False
    assert spec.option_relative_time == True

    spec1 = ticket_lib.TicketSpec(ticket_spec_dict)

    assert spec1 == spec

    dat = spec1.serialize()
    _, spec2 = ticket_lib.TicketSpec.from_serialized_data(0, dat)

    assert spec2 == spec1 == spec

    ticket_spec_dict = {
        'description': "Whatever",
    }

    spec = ticket_lib.TicketSpec(ticket_spec_dict)

    assert not spec2 == spec

    assert spec.value == 0
    assert spec.book_of == 1
    assert spec.time_to_begin == 0
    assert spec.time_to_end == ticket_lib.Constants.MAX_INT64
    assert spec.expire_after == 0
    assert spec.option_divisible == False
    assert spec.option_relative_time == False

    ticket_spec_dict = {
        'description': 123,
    }

    try:
        spec = ticket_lib.TicketSpec(ticket_spec_dict)
    except TypeError:
        spec = 10

    assert spec == 10

    ticket_spec_dict = {
        'description': "Yokohama Municipal Subway Regular Multiple",
        'value': 270,
        'unit': 1
    }

    try:
        spec = ticket_lib.TicketSpec(ticket_spec_dict)
    except TypeError:
        spec = 101

    assert spec == 101

    ticket_spec_dict = {
        'description': "Yokohama Municipal Subway Regular Multiple",
        'value': "12"
    }

    try:
        spec = ticket_lib.TicketSpec(ticket_spec_dict)
    except TypeError:
        spec = 11

    assert spec == 11

    ticket_spec_dict = {
        'description': "Yokohama Municipal Subway Regular Multiple",
        'value': 0x8000000000000000
    }

    try:
        spec = ticket_lib.TicketSpec(ticket_spec_dict)
    except TypeError:
        spec = 12

    assert spec == 12

    ticket_spec_dict = {
        'description': "Yokohama Municipal Subway Regular Multiple",
        'book_of': "3"
    }

    try:
        spec = ticket_lib.TicketSpec(ticket_spec_dict)
    except TypeError:
        spec = 13

    assert spec == 13

    ticket_spec_dict = {
        'description': "Yokohama Municipal Subway Regular Multiple",
        'book_of': 0
    }

    try:
        spec = ticket_lib.TicketSpec(ticket_spec_dict)
    except TypeError:
        spec = 14

    assert spec == 14

    ticket_spec_dict = {
        'description': "Yokohama Municipal Subway Regular Multiple",
        'time_to_begin': "now"
    }

    try:
        spec = ticket_lib.TicketSpec(ticket_spec_dict)
    except TypeError:
        spec = 15

    assert spec == 15

    ticket_spec_dict = {
        'description': "Yokohama Municipal Subway Regular Multiple",
        'time_to_begin': -1
    }

    try:
        spec = ticket_lib.TicketSpec(ticket_spec_dict)
    except TypeError:
        spec = 16

    assert spec == 16

    ticket_spec_dict = {
        'description': "Yokohama Municipal Subway Regular Multiple",
        'time_to_end': "never"
    }

    try:
        spec = ticket_lib.TicketSpec(ticket_spec_dict)
    except TypeError:
        spec = 17

    assert spec == 17

    ticket_spec_dict = {
        'description': "Yokohama Municipal Subway Regular Multiple",
        'time_to_end': 0
    }

    try:
        spec = ticket_lib.TicketSpec(ticket_spec_dict)
    except TypeError:
        spec = 18

    assert spec == 18

    ticket_spec_dict = {
        'description': "Yokohama Municipal Subway Regular Multiple",
        'expire_after': "never"
    }

    try:
        spec = ticket_lib.TicketSpec(ticket_spec_dict)
    except TypeError:
        spec = 19

    assert spec == 19

    ticket_spec_dict = {
        'description': "Yokohama Municipal Subway Regular Multiple",
        'expire_after': -1
    }

    try:
        spec = ticket_lib.TicketSpec(ticket_spec_dict)
    except TypeError:
        spec = 20

    assert spec == 20

    ticket_spec_dict = {
        'description': "Yokohama Municipal Subway Regular Multiple",
        'option_divisible': "yes"
    }

    try:
        spec = ticket_lib.TicketSpec(ticket_spec_dict)
    except TypeError:
        spec = 21

    assert spec == 21

    ticket_spec_dict = {
        'description': "Yokohama Municipal Subway Regular Multiple",
        'option_relative_time': "yes"
    }

    try:
        spec = ticket_lib.TicketSpec(ticket_spec_dict)
    except TypeError:
        spec = 22

    assert spec == 22


def test_ticket():

    description = "SpecialExpress:Nozomi 41:ShinYokohama:Kyoto:Car 9:Seat 13A"
    value = 1
    unit = "person"
    book_of = 1
    time_to_begin = 1552888140
    time_to_end = 1552895220
    expire_after = 60 * 60 * 24 * 3

    ticket_spec_dict = {
        'description': description,
        'value': value,
        'unit': unit,
        'book_of': book_of,
        'time_to_begin': time_to_begin,
        'time_to_end': time_to_end,
        'expire_after': expire_after,
    }

    spec = ticket_lib.TicketSpec(ticket_spec_dict)

    ticket = ticket_lib.Ticket(spec=spec, time_of_origin=1552885200)

    dat = ticket.serialize()
    _, ticket = ticket_lib.Ticket.from_serialized_data(0, dat)

    assert ticket.ticket_id is None
    assert ticket.spec == spec
    assert ticket.time_of_origin == 1552885200

    ticket.ticket_id = hashlib.sha256(dat).digest()
    ticket_id = hashlib.sha256(dat).digest()

    dat = ticket.serialize()
    _, ticket = ticket_lib.Ticket.from_serialized_data(0, dat)

    assert ticket.ticket_id == ticket_id
    assert ticket.spec is None
    assert ticket.time_of_origin is None


def test_ticket_attributes():

    description = "SpecialExpress:Nozomi 41:ShinYokohama:Kyoto:Car 9:Seat 13A"
    value = 1
    unit = "person"
    book_of = 1
    time_to_begin = 1552888140
    time_to_end = 1552895220
    expire_after = 60 * 60 * 24 * 3

    ticket_spec_dict = {
        'description': description,
        'value': value,
        'unit': unit,
        'book_of': book_of,
        'time_to_begin': time_to_begin,
        'time_to_end': time_to_end,
        'expire_after': expire_after,
        'option_divisible': True,
        'option_transferable': False,
        'option_relative_time': True,
    }

    spec = ticket_lib.TicketSpec(ticket_spec_dict)

    ticket = ticket_lib.Ticket(spec=spec, time_of_origin=1552885200)

    assert ticket.is_divisible()
    assert not ticket.is_transferable()
    assert ticket.is_relative_time()

    ticket_spec_dict = {
        'description': description,
        'value': value,
        'unit': unit,
        'book_of': book_of,
        'time_to_begin': time_to_begin,
        'time_to_end': time_to_end,
        'expire_after': expire_after,
        'option_divisible': False,
        'option_transferable': True,
        'option_relative_time': False,
    }

    spec = ticket_lib.TicketSpec(ticket_spec_dict)

    ticket = ticket_lib.Ticket(spec=spec, time_of_origin=1552885200)

    assert not ticket.is_divisible()
    assert ticket.is_transferable()
    assert not ticket.is_relative_time()


def test_service():

    service = ticket_lib.BBcTicketService(domain_id, service_id, service_id,
            idPubkeyMap)

    user_a_id, keypairs_a = idPubkeyMap.create_user_id(num_pubkeys=1)
    user_b_id, keypairs_b = idPubkeyMap.create_user_id(num_pubkeys=1)

    ticket_spec_dict = {
        'description': "Denki Groove:Zepp Tokyo:S3-16:Open 1552640400",
        'value': 1,
        'unit': "person",
        'book_of': 1,
        'time_to_begin': 1552644000,
        'time_to_end': 1552654800,
        'expire_after': 0,
    }

    spec = ticket_lib.TicketSpec(ticket_spec_dict)

    ticket_id, _ = service.issue(user_a_id, spec, time_of_origin=1552600000,
            keypair=keypairs[0])

    assert service.is_valid_holder(user_a_id, ticket_id)

    service.transfer(user_a_id, user_b_id, ticket_id,
            keypair_from=keypairs_a[0], keypair_service=keypairs[0])

    assert service.is_valid_holder(user_b_id, ticket_id)
    assert not service.is_valid_holder(user_a_id, ticket_id)

    service.redeem(user_b_id, ticket_id, keypair_from=keypairs_b[0],
            keypair_service=keypairs[0])

    assert service.is_valid_holder(service_id, ticket_id)


def test_transferable():

    service = ticket_lib.BBcTicketService(domain_id, service_id, service_id,
            idPubkeyMap)

    user_a_id, keypairs_a = idPubkeyMap.create_user_id(num_pubkeys=1)
    user_b_id, keypairs_b = idPubkeyMap.create_user_id(num_pubkeys=1)

    ticket_spec_dict = {
        'description': "Denki Groove:Zepp Tokyo:S3-16:Open 1552640400",
        'value': 1,
        'unit': "person",
        'book_of': 1,
        'time_to_begin': 1552644000,
        'time_to_end': 1552654800,
        'expire_after': 0,
        'option_transferable': False,
    }

    spec = ticket_lib.TicketSpec(ticket_spec_dict)

    ticket_id, _ = service.issue(user_a_id, spec, time_of_origin=1552600000,
            keypair=keypairs[0])

    assert service.is_valid_holder(user_a_id, ticket_id)

    ticket_id2 = hashlib.sha256(ticket_id).digest()

    try:
        service.transfer(user_a_id, user_b_id, ticket_id2,
                keypair_from=keypairs_a[0], keypair_service=keypairs[0])
    except TypeError:
        spec = 10

    assert spec == 10

    try:
        service.transfer(user_a_id, user_b_id, ticket_id,
                keypair_from=keypairs_a[0], keypair_service=keypairs[0])
    except TypeError:
        spec = 11

    assert spec == 11


# end of tests/test_ticket_lib.py
