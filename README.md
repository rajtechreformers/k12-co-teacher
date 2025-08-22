# k12-co-teacher
In K-12 classrooms, teachers are responsible for meeting the diverse needs of all learners ranging from students receiving special education services and those with 504 accommodations, to English language learners and gifted and talented students who require enrichment. Each of these groups comes with distinct supports and instructional considerations that must be applied consistently for students to succeed.  This solution provides an AI-powered classroom assistant tha helps teachers quickly generate differentiated lesson plans and respond to student needs.  Using Individual Education Plans (IEPs), 504 plans, and evaluation reports the solution extracts and highlights concise modifications to an existing lesson plan for the teacher.  AWS Lambda and Amazon API Gateway provide backend application logic, while Amazon DynamoDB stores student profiles, class rosters, teacher notes, and chat history. Authentication and access are managed with Amazon Cognito, and the application is deployed with AWS Amplify. 


### Table of contents

- [Licence](#licence)
- [Key Features](#key-features)
- [Architecture overview](#architecture-overview)
  - [Architecture reference diagram](#architecture-reference-diagram)
  - [Solution components](#solution-components)
- [Prerequisites](#prerequisites)
  - [Build environment specifications](#build-environment-specifications)
  - [AWS account](#aws-account)
  - [Tools](#tools)
- [How to build and deploy the solution](#how-to-build-and-deploy-the-solution)
  - [Configuration](#configuration)
  - [Build and deploy](#build-and-deploy)
- [File structure](#file-structure)

---

## Collaboration

Thanks for your interest in our solution. Having specific examples of replication and cloning allows us to continue to grow and scale our work. If you clone or download this repository, kindly shoot us a quick email to let us know you are interested in this work!

[wwps-cic@amazon.com]

---

# Disclaimers

**Customers are responsible for making their own independent assessment of the information in this document.**

**This document:**

(a) is for informational purposes only,

(b) represents current AWS product offerings and practices, which are subject to change without notice, and

(c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS products or services are provided “as is” without warranties, representations, or conditions of any kind, whether express or implied. The responsibilities and liabilities of AWS to its customers are controlled by AWS agreements, and this document is not part of, nor does it modify, any agreement between AWS and its customers.

(d) is not to be considered a recommendation or viewpoint of AWS

**Additionally, all prototype code and associated assets should be considered:**

(a) as-is and without warranties

(b) not suitable for production environments

(d) to include shortcuts in order to support rapid prototyping such as, but not limitted to, relaxed authentication and authorization and a lack of strict adherence to security best practices

**All work produced is open source. More information can be found in the GitHub repo.**

## Authors and Acknowledgements

### Modified by:

- Noor Dhaliwal - rdhali07@calpoly.edu
- Sharon Liang - sliang19@calpoly.edu


## Licence

Licensed under the Apache License Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://www.apache.org/licenses/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.

## Key Features

1 . . .

## Architecture overview

### Architecture reference diagram

The following diagram represents the solution's architecture design.

![Diagram](docs/images/solution_architecture_diagram.png)

### Solution components


- **Amazon Bedrock**: Provides access to:
  - Foundation Models for text generation


## Prerequisites

### Build environment specifications

- To build and deploy this solution. . .


### Tools

- The latest version of the [AWS CLI](https://aws.amazon.com/cli/), installed and configured.
- The latest version of the [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/home.html).
- [Nodejs](https://docs.npmjs.com/getting-started) version 18 or newer.
- [Docker](https://docs.docker.com/get-docker/)


### 1- Bedrock model persmissions

```markdown
### Enable Bedrock Model Access

1. **Navigate to Bedrock Console**

   - Sign in to AWS Management Console
   - Go to Amazon Bedrock console: https://console.aws.amazon.com/bedrock/
   - Select "Model access" from the left navigation pane

2. **Request Model Access**

   - Click on "Edit" button in top right
   - Select the required models (Check config.yaml file):
     -us.meta.llama3-3-70b-instruct-v1:0
     -us.amazon.nova-pro-v1:0
     -us.anthropic.claude-3-5-sonnet-20241022-v2:0
     -us.anthropic.claude-3-7-sonnet-20250219-v1:0
     -cohere.rerank-v3-5:0
     -amazon.titan-embed-text-v2:0
   - Click "Save changes"
   - Wait for access approval (usually immediate)

3. **Verify Model Access**

   - Return to "Model access" page
   - Confirm selected models show "Access granted" status
   - Models should now be available for use in the solution

4. **Region Considerations**

   - Ensure model access is enabled in the same region where you plan to deploy
   - If deploying to a different region, repeat process to enable models there
   - Some models may not be available in all regions

5. **Required Permissions**
   - IAM user must have sufficient permissions to request model access
   - Recommended to use admin permissions during initial setup
```

---

## How to build and deploy the solution

Before you deploy the solution, review the architecture and prerequisites sections in this guide. Follow the step-by-step instructions in this section to configure and deploy the solution into your account.

Time to deploy: approximately 20 minutes

### Authenticate for AWS deployment

```bash
AWS configure
```

Provide the Access key and secret, For Region select us-east-1 ( or region of your choice)

### Get the code on your dev machine

```bash
git clone https://github.com/cal-poly-dxhub/k12-co-teacher.git
```

Change the directory to code directory

```bash
 cd k12-co-teacher/
```

### Build the code

Install the dependencies

```bash
npm install
```

Deploy the solution
. . .

## Support

For any queries or issues, please contact:
- Darren Kraker, Sr Solutions Architect - <dkraker@amazon.com>
- Noor Dhaliwal, Software Development Engineer Intern - <rdhali07@calpoly.edu>
- Sharon Liang, Software Development Engineer Intern - <sliang19@calpoly.edu>


Licensed under the Apache License Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://www.apache.org/licenses/

or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.
