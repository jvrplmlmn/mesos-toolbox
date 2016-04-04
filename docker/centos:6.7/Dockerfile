FROM centos:6.7

RUN yum install -y centos-release-scl \
  && echo -e '[WANdiscoSVN]\n\
name=WANdisco SVN Repo 1.9\n\
enabled=1\n\
baseurl=http://opensource.wandisco.com/centos/6/svn-1.9/RPMS/$basearch/\n\
gpgcheck=1\n\
gpgkey=http://opensource.wandisco.com/RPM-GPG-KEY-WANdisco\n' >> /etc/yum.repos.d/wandisco-svn.repo \
  && yum install -y \
    apr-devel \
    apr-util-devel \
    cyrus-sasl-devel \
    cyrus-sasl-md5 \
    devtoolset-3-gcc \
    devtoolset-3-gcc-c++ \
    git \
    java-1.8.0-openjdk-devel \
    libcurl-devel \
    maven30 \
    nss \
    openssl-devel \
    patch \
    python-devel \
    ruby-devel \
    rubygems \
    subversion-devel \
    tar \
    which \
    wget \
    zlib-devel \
  && source scl_source enable devtoolset-3 \
  && gem install fpm --no-ri --no-rdoc -V

ENV PATH /opt/rh/maven30/root/usr/bin:/opt/rh/devtoolset-3/root/usr/bin${PATH:+:${PATH}}
ENV JAVA_HOME /usr/lib/jvm/java-1.8.0-openjdk
