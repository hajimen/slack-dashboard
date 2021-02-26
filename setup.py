from setuptools import setup

setup(
    name="slack-dashboard",
    version="0.1.1",
    description="Slack dashboard",
    install_requires=[
        "slackclient==1.3.2",
        "appdirs==1.4.3",
    ],
    packages=['slack_dashboard'],
    entry_points={
        'console_scripts': [
            'slack-dashboard=slack_dashboard.main:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ]
)
