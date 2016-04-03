FROM centos:6.7

RUN yum install -y tar wget git which nss \
    && yum install -y centos-release-scl  \
    && yum install -y devtoolset-3-gcc \
    && ln -sf /opt/rh/devtoolset-3/root/usr/bin/gcc /usr/bin/gcc \
    && echo -e '[WANdiscoSVN]\n\
name=WANdisco SVN Repo 1.9\n\
enabled=1\n\
baseurl=http://opensource.wandisco.com/centos/6/svn-1.9/RPMS/$basearch/\n\
gpgcheck=1\n\
gpgkey=http://opensource.wandisco.com/RPM-GPG-KEY-WANdisco\n' >> /etc/yum.repos.d/wandisco-svn.repo \
    && yum install -y apache-maven python-devel java-1.8.0-openjdk-devel zlib-devel libcurl-devel openssl-devel cyrus-sasl-devel cyrus-sasl-md5 apr-devel subversion-devel apr-util-devel ruby-devel rubygems \
    && gem install fpm --no-ri --no-rdoc

ENV JAVA_HOME /usr/lib/jvm/java-1.8.0-openjdk
