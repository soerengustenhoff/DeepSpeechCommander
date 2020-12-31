import logging
import deepspeech
import os
import deepSpeechModels


def init(args, data_model: deepSpeechModels.DeepSpeechDataModel):
    # Load DeepSpeech model
    if os.path.isdir(args.model):
        model_dir = args.model
        args.model = os.path.join(model_dir, 'output_graph.pb')
        args.scorer = os.path.join(model_dir, args.scorer)

    print('Initializing model...')
    logging.info("ARGS.model: %s", args.model)
    model = deepspeech.Model(args.model)
    if args.scorer:
        logging.info("ARGS.scorer: %s", args.scorer)
        model.enableExternalScorer(args.scorer)

    data_model.model = model
    return data_model
