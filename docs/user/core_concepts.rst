*************
Core Concepts
*************

Before delving into the depths of the experiment Support System, it is
worthwhile to briefly cover the core concepts used in the experiment Support
System and how they interact with each other.

The central element in the experiment Support System is the :term:`experiment`.
The :term:`experiment` is created by the :term:`researcher`, who then
recruites the :term:`participants` who generate the :term:`experiment`'s
:term:`results`.

Each :term:`experiment` consists of one or more :term:`pages`. In the
:term:`experiment` these :term:`pages` are linked together to define
the :term:`experiment` participants' path through the :term:`experiment`. On
each :term:`page` the participants are shown a series of :term:`questions`.
The :term:`questions` can either be used to present the participants with
information or to request the participants to provide responses to specific
prompts or questions.

:term:`Experiments` can have :term:`data` attached to them, enabling the
creation of flexible, data-driven :term:`experiments`. The Experiment
Support System supports two types of :term:`data`. Basic :term:`data sets`
consist of lists of :term:`data items` and can be attached to individual
:term:`pages`. Each :term:`data items` attributes can then be used in the
questions or information shown to the participants. :term:`Permutation sets`
are automatically derived from two source :term:`data sets` and can be used to
create complex experiments that use a latin-square to ensure that participants
responses to stimuli are balanced.

.. glossary::
  :sorted:

  Data
    :term:`Experiments` can have data attached to them, in order to support
    the creation of flexible, data-driven :term:`experiments`. The Experiment
    Support System supports two kinds of data: :term:`data sets` and
    :term:`permutation sets`.
    
  Data Item
  Data Items
    A data item is a set of key - value attributes that are grouped into one
    item and that can be accessed in a :term:`page` that has been linked to the
    :term:`data set` the data items belong to.
    
  Data Set
  Data Sets
    Basic data sets are lists of :term:`data items`, that can be used in
    :term:`pages` to create data-driven :term:`experiments`.
  
  Experiment
  Experiments
    The core element of the experiment Support System is defined as a set of
    :term:`pages` that are linked together to define the experiment that the
    :term:`participants` provide :term:`results` for. 
  
  Page
  Pages
    A page in an :term:`experiment` consists of one or more :term:`questions`.
    pages are linked together to form the complete :term:`experiment` and the
    transitions between pages define the participants' path through the
    :term:`experiment`. 
  
  Participant
  Participants
    The participants are people recruited by the :term:`researcher` to
    participate in an :term:`experiment`
  
  Permutation set
  Permutation sets
    Permutation sets are used to create latin-square based, balanced
    :term:`experiments`. They are derived from two basic :term:`data sets`
    based on constraints set up when the permutation set is created.
    
  Question
  Questions
    A question either shows information to the :term:`experiment` participants
    or requests that the participants provide a response to a prompt or
    question. The experiment Support System comes with a default set of
    questions, but additional question sets can be added.
  
  Researcher
    The researcher is an Experiment Support System user who creates
    :term:`experiments`, invites :term:`participants`, and processes
    :term:`results`.
    
  Result
  Results
    When each :term:`participant` interacts with the :term:`experiment`, the
    responses are stored by the Experiment Support System and form the results
    that the :term:`researcher` can download and then process to evaluate the
    :term:`experiment`'s output.
  