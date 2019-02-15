def user_password(strategy, user,is_new=False, *args, details, backend, **kwargs):
    if backend.name != 'username':
        return
    details['username'] = name = strategy.request_data()['username']
    details['first_name'] = 'Max'
    details['last_name'] = 'Mustermann'
    details['email'] = name+'@test.com'
    details['fullname'] = 'Max Mustermann'
