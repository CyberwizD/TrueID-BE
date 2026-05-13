insert into caller_profiles (
    phone_number, display_name, city, state, country, spam_score, confidence_score, is_business, verified
)
values
    ('+2348030001111', 'Kora Logistics', 'Victoria Island', 'Lagos', 'Nigeria', 18, 88, true, true),
    ('+2348091234567', 'Chiamaka Okafor', 'Gwarinpa', 'FCT', 'Nigeria', 4, 74, false, false),
    ('+2347011112222', 'QuickCash Loans', 'Ikeja', 'Lagos', 'Nigeria', 72, 79, true, false)
on conflict (phone_number) do nothing;

insert into contact_contributions (
    user_id, phone_number, contact_name, source_city, source_state
)
values
    ('user_ada', '+2348091234567', 'Chiamaka Okafor', 'Gwarinpa', 'FCT'),
    ('user_emeka', '+2348091234567', 'Chiamaka', 'Abuja', 'FCT'),
    ('user_bisi', '+2348112223334', 'Dr Tolu Dental', 'Yaba', 'Lagos'),
    ('user_ife', '+2348112223334', 'Tolu Dental Clinic', 'Sabo', 'Lagos')
on conflict do nothing;

insert into spam_reports (
    reporter_id, phone_number, reason, notes
)
values
    ('user_uche', '+2347011112222', 'loan_spam', 'Aggressive repeat loan calls'),
    ('user_sarah', '+2347011112222', 'telemarketing', null);
