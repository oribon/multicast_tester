# multicast-tester
An app that tests multicast capabilities in an Openshift project.
* Creates a daemonset in the project.
* Tells all of the daemonset's pods what's up its from the pizza using multicast.
* The pods should respond with their hostnames.
* Deletes the daemonset.
* Sends Splunk a summary of what happened.
* ~ Tested on Openshift 4.2 ~

## Prerequisites
* Create a namespace called multicast-test.
    * oc new-project multicast-test
* Annotate the project to support multicast
    *   oc annotate netnamespace multicast-test netnamespace.network.openshift.io/multicast-enabled=true
* Create a service account called multicast-user in the project and give him admin permissions in the project.
    *  oc create serviceaccount multicast-user
    *  oc create rolebinding multicast-binding --clusterrole=admin --serviceaccount=multicast-test:multicast-user --namespace=multicast-test
* Create a secret named multicast-secret with the following params
    * SPLUNK_API_URL
    * SPLUNK_TOKEN
    * VERIFY_SPLUNK_SSL

## Manual trigger of CronJob
* oc create job --from=cronjob/test-multicast test-multicast