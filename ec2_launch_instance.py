import os
import time
import boto
import boto.manage.cmdshell
def launch_instance(ami='ami-7341831a',
                    instance_type='t1.micro',
                    key_name='admin',
                    key_extension='.pem',
                    key_dir='~/.ssh',
                    group_name='admin',
                    ssh_port=22,
                    cidr='0.0.0.0/0',
                    tag='paws',
                    user_data=None,
                    cmd_shell=True,
                    login_user='ec2-user',
                    ssh_passwd=None):
    cmd = None
    
    ec2 = boto.connect_ec2()

    try:
        key = ec2.get_all_key_pairs(keynames=[key_name])[0]
    except ec2.ResponseError, e:
        if e.code == 'InvalidKeyPair.NotFound':
            print 'Creating keypair: %s' % key_name
            # Create an SSH key to use when logging into instances.
            key = ec2.create_key_pair(key_name)
            
            # AWS will store the public key but the private key is
            # generated and returned and needs to be stored locally.
            # The save method will also chmod the file to protect
            # your private key.
            key.save(key_dir)
        else:
            raise

    try:
        group = ec2.get_all_security_groups(groupnames=[group_name])[0]
    except ec2.ResponseError, e:
        if e.code == 'InvalidGroup.NotFound':
            print 'Creating Security Group: %s' % group_name
            # Create a security group to control access to instance via SSH.
            group = ec2.create_security_group(group_name,
                                              'A group that allows SSH access')
        else:
            raise

    try:
        group.authorize('tcp', ssh_port, ssh_port, cidr)
    except ec2.ResponseError, e:
        if e.code == 'InvalidPermission.Duplicate':
            print 'Security Group: %s already authorized' % group_name
        else:
            raise

    reservation = ec2.run_instances(ami,
                                    key_name=key_name,
                                    security_groups=[group_name],
                                    instance_type=instance_type,
                                    user_data=user_data)


    instance = reservation.instances[0]


    print 'waiting for instance'
    while instance.state != 'running':
        print '.'
        time.sleep(5)
        instance.update()
    print 'done'

    instance.add_tag(tag)

    
    if cmd_shell:
        key_path = os.path.join(os.path.expanduser(key_dir),
                                key_name+key_extension)
        cmd = boto.manage.cmdshell.sshclient_from_instance(instance,
                                                          key_path,
                                                          user_name=login_user)
                                                            
    return (instance, cmd)

launch_instance()
