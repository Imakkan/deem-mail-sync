# Email Adapter

the purpose of email adapter is to allow communication between http web services to email protocol 'IMAP' and 'SMTP'

## requests

all request is post request with common top level attribute:

- command
- arguments

## commands

### List MailBoxes

command that return the list of mail boxes the user have, each box has:

- name: the name of the mailbox (folder)
- messages: th number of messages (read and unread)
- unseen: the number of unread messages
- recent: the number of new messages since the last fetch

#### request:

```
{
    "command": "LIST_MAILBOX", // string
    "arguments": {} // empty object
}
```

#### response:

```
[
    {
        "name": "INBOX", // string
        "messages": 0, // integer
        "unseen": 0, // integer
        "recent": 0 // integer
    }
]
```

### Create Custom MailBox

command that create custom mailbox

#### request:

```
{
    "command": "CREATE_MAILBOX", // string
    "arguments": {
        "mailbox": "some name" // string
    } 
}
```

#### response:

```
```


### Rename Custom MailBox

command that rename custom mailbox

#### request:

```
{
    "command": "CREATE_MAILBOX", // string
    "arguments": {
        "mailbox": "some name" // string
        "new_name": "new name" // string
    } 
}
```

#### response:

```
```

### Delete Custom MailBox

command that delete custom mailbox

#### request:

```
{
    "command": "CREATE_MAILBOX", // string
    "arguments": {
        "mailbox": "mailbox name" // string
    } 
}
```

#### response:

```
```

### List MAILS

command that return the paginated list of mails the user have, each mail has:

- subject: email's subject
- flags: list of flags on specific mail
- sender: sender's email
- brief: first 100 chars from message
- uid: email id
- attachments: list of attachments
- date: date and time of the message

#### request:

```
{
    "command" : "LIST_MAIL",    // str
    "arguments": {
        "mailbox": "INBOX",     // str
        "page": 1,              // int
        "limit": 10,            // int
        "search_query": "SUBJECT test"      // optional 
    }
}
```

#### response:

```
{
    "total_pages": 1,
    "total_items": 3,
    "current_page": 1,
    "items": [
        {
            "flags": [                      // List
                "\\Seen"
            ],
            "subject": "test",              // str
            "date": "2021-10-07 09:35:06",  //datetime
            "sender": "user1@home.org",     // str
            "to": [                         // list
                "user1@home.org"
            ],
            "cc": [                         // list
                "user3@home.org",
                "user4@home.org"
            ],
            "bcc": [],                      // list
            "brief": "",                    // str
            "uid": 1,                       // int
            "attachment": [                 // list
                {
                    "part_number": "2",       // str
                    "content_type": "application/pdf",
                    "content_name": "report.pdf",
                    "content_size": 4146
                }
            ]
        }
    ]
}

```

### Peek MAIL

command that return the fetch one mail with limited information for notification:

- subject: email's subject
- flags: list of flags on specific mail
- sender: sender's email
- brief: first 100 chars from message
- uid: email id
- attachments: list of attachments
- date: date and time of the message

#### request:

```
{
    "command" : "PEEK_MAIL",    // str
    "arguments": {
        "mailbox": "INBOX",     // str
        "mail_uid": 1,              // int
    }
}
```

#### response:

```
{
    "flags": [                      // List
        "\\Seen"
    ],
    "subject": "test",              // str
    "date": "2021-10-07 09:35:06",  //datetime
    "sender": "user1@home.org",     // str
    "to": [                         // list
        "user1@home.org"
    ],
    "cc": [                         // list
        "user3@home.org",
        "user4@home.org"
    ],
    "bcc": [],                      // list
    "brief": "",                    // str
    "uid": 1,                       // int
    "attachment": [                 // list
        {
            "part_number": "2",       // str
            "content_type": "application/pdf",
            "content_name": "report.pdf",
            "content_size": 4146
        }
    ]
}

```
### Fetch MAIL

command return mail as json by mail_uid:

- body: email's body as text
- headers: list of headers
- attachment: list of attachments

#### request:

```
{
    "command": "FETCH_MAIL", // string
    "arguments": {
        "mailbox": "Sent" // str
        "mail_uid": 1     // int
    } 
}
```

#### response:

```
{
    "uid": 1,
    "body": "testing",
    "flags": [
        "\\Seen"
    ],
    "headers": [
        {
            "name": "MIME-Version",
            "value": "1.0"
        },
        {
            "name": "Date",
            "value": "Mon, 11 Oct 2021 13:34:59 +0300"
        },
        {
            "name": "From",
            "value": "user1@home.org"
        },
        {
            "name": "To",
            "value": "user1@home.org, user2@home.org, user3@home.org"
        },
        {
            "name": "Cc",
            "value": "user100@home.org, user102@home.org"
        },
        {
            "name": "Subject",
            "value": "test"
        },
        {
            "name": "User-Agent",
            "value": "Roundcube Webmail/1.4.11"
        },
        {
            "name": "Message-ID",
            "value": "<26f004a43e51f616659ca4badc737ab0@home.org>"
        },
        {
            "name": "X-Sender",
            "value": "user1@home.org"
        },
        {
            "name": "Content-Type",
            "value": "text/plain; charset=US-ASCII;\nformat=flowed"
        },
        {
            "name": "Content-Transfer-Encoding",
            "value": "7bit"
        }
    ],
    "attachment": [
            {
                "part_number": "2",       // str
                "content_type": "application/pdf",
                "content_name": "report.pdf",
                "content_size": 4146
            }
    ]}
```

### Send MAIL

command return None:

- body: email's body as text
- styled_body: email's styled body "optional" as text
- headers: list of headers
- attachment: Optional list of attachments
- recipients: list of recipient's email

#### request:

```
{
    "command" : "SEND_MAIL",                                  // str 
    "arguments": {
        "recipients": ["user1@home.org"],                    // List[str]
        "body": "str body",                                  // str
        "headers": [                                        // List[dict]
                    {"name": "subject", "value": "str"},     
                    {"name": "To", "value": "User 1 <user1@home.org>"},
                    {"name": "Cc", "value": "User 2 <user2@home.org>"},
                    {"name": "Date", "value": "Mon, 18 Oct 2021 11:33:18 +0000 (UTC)"}
                  ],                                                
        "attachments" : [      // List[dict]
                    {
                        "content": "some data",     // str
                        "content_type": "application/pdf", // str
                        "content_name": "blank.pdf", // str
                        "content_size": 4911,  // int size in bytes
                    }
        ]
    }
}

```

### Append MAIL

command return None:

- body: email's body as text
- styled_body: email's styled body "optional" as text
- headers: list of headers
- attachment: Optional list of attachments
- mailbox: target mailbox to store the mail message

#### request:

```
{
    "command" : "APPEND_MAIL",                                  // str 
    "arguments": {
        "mailbox": "Sent",                    // str
        "body": "some message body",                                  // str
        "headers": [                                        // List[dict]
                    {"name": "subject", "value": "str"},     
                    {"name": "To", "value": "User 1 <user1@home.org>"},
                    {"name": "Cc", "value": "User 2 <user2@home.org>"},
                    {"name": "Date", "value": "Mon, 18 Oct 2021 11:33:18 +0000 (UTC)"}
                  ]                                                
        }
        "attachments" : [      // List[dict]
                    {
                        "content": "some data",     // str
                        "content_type": "application/pdf", // str
                        "content_name": "blank.pdf", // str
                        "content_size": 4911,  // int size in bytes
                    }
        ]
}

```

### Copy MAIL

copy a mails from mailbox to mailbox
command return None:

- mailbox: source mailbox to copy mails message from
- mail_uid: source mail uids as list
- target_mailbox: target mailbox to copy mails message into

#### request:

```
{
    "command" : "COPY_MAIL", // str 
    "arguments": {
        "mailbox": "INBOX", // str
        "mail_uid": [1,2,3], // list of int
        "target_mailbox": "Deleted" // str
        }
}

```

### Delete MAIL

delete a mails from mailbox
command return None:

- mailbox: source mailbox to delete mails message from
- mail_uid: source mail uids

#### request:

```
{
    "command" : "DELETE_MAIL", // str 
    "arguments": {
        "mailbox": "INBOX", // str
        "mail_uid": [1,2,3], // int
        }
}

```

### Add Flags

add list of flags to list of mails in mailbox command return None:

- mailbox: the name of the mailbox (folder)
- mail_uid: list of existing mail uids
- flags: list of valid flags

#### request:

```
{
    "command" : "ADD_FLAGS",                // str
    "arguments": {
        "mailbox": "Inbox",                 // str
        "mail_uid": [1,2],                  // List[int]
        "flags": ["\\Seen", "\\Answered"]   // List[str]
        }
}

```

### Remove Flags

add list of flags to list of mails in mailbox command return None:

- mailbox: the name of the mailbox (folder)
- mail_uid: list of existing mail uids
- flags: list of valid flags

#### request:

```
{
    "command" : "REMOVE_FLAGS",                // str
    "arguments": {
        "mailbox": "Inbox",                 // str
        "mail_uid": [1,2],                  // List[int]
        "flags": ["\\Seen", "\\Answered"]   // List[str]
        }
}

```

### All Commands

- LIST_MAIL
- FETCH_MAIL
- DELETE_MAIL
- COPY_MAIL
- SEND_MAIL
- APPEND_MAIL
- CREATE_MAILBOX
- DELETE_MAILBOX
- LIST_MAILBOX
- DOWNLOAD_ATTACHMENT

## FLAGS

- **\Seen**: Message has been read.
- **\Flagged**: Message is marked as “flagged” for urgent/special attention.
- **\Recent**: Message is "recently" arrived in this mailbox in this session.
- **\Answered**: Message has been answered.
- **\Deleted**: Message is marked as “to be deleted”.
- **\Draft**: Message has not completed composition (marked as a draft).
