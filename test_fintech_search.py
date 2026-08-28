from fintech_search import PaymentEvent, decide_payment


def test_foreign_large_payment_is_sent_to_review():
    event = PaymentEvent(event_id="pay_test", merchant="Orbital Parts", amount_usd=1800, country="SG", note="urgent wire")
    decision = decide_payment(event)
    assert decision.action == "manual_review"
    assert decision.event_id == "pay_test"
    assert "pay_test" in decision.audit_message
