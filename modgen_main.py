import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from modgen_utils import *
from modgen_classifier_models import *
from tqdm import tqdm_notebook as tqdm
import warnings
warnings.filterwarnings(action='ignore', category=DeprecationWarning)

######################### Path / Train / Test Data ###########################

### Path for all documents to be used/exported from this program.
# - train.csv                 : Train Data for training/validation sets
# - test.csv                  : Test Data to be predicted
# - analysis_df.csv           : DataFrame of all 'params' used for each model generated.  Can be recalled.
# - prediction_submission.csv : Prediction of test data
path = '~/Documents/'
train = pd.read_csv(path + "train.csv")
test = pd.read_csv(path + "test.csv")

##################### Feature Engineering Code Goes Here #####################





##################### Feature Engineering Code Goes Here #####################

######## Model Options ########
# Classification or Regression
is_classifier = True

### K-Fold Options:
# 'normal', 'strat', 'normal_repeat', 'strat_repeat' - (type, # repeats)
use_kfold_CV = False
kfold_number_of_folds = 5
kfold_distribution = 'normal'
kfold_repeats = 1

### Data Split Options: Train/Validation split (Non-KFold)
# Percentage of total data to be used in the validation set (train set automatically set 1 - split_valid_size)
split_valid_size = 0.25
stratify_data = False

### Scaler Option: StandardScaler(), Normalizer(), MinMaxScaler(), RobustScaler()
# If scaler_select = None, then no scaling will be done
scaler_select = StandardScaler()

### Model Creation Options:
# use_previous_model = False: Use new models_to_be_created dictionary to make models listed, else, use previous index to get parameters
# train_test_submission = True: Train data on test set and make submission file of results
# submission_column_names: The key and predicted value column names for submission file
# ensemble = True: Ensemble all previous index models together [NOT CURRENTLY WORKING]
use_previous_model = True
train_test_submission = True
submission_column_names = ('PassengerId','Survived')
ensemble = False

params = {}
if use_previous_model:
    params, model_selector, model_selector_mod = getSavedParams(path, load_index = 2)
    models_to_be_created = {model_selector : 1}
else:
    models_to_be_created = {
                        'lightgbm'     : 100,
                        'xgboost'      : 100,
                        'knn'          : 50,
                        'svm'          : 50,
                        'decisiontree' : 50,
                        'randomforest' : 50,
#                        'neuralnetwork': 5,
#                        'gradboost'    : 5,
#                         'lasso'        : 500,
#                         'ridge'        : 500,
                    }

## In place until bug is fixed in dataFrameUpdate() function when using KFold and NN
bug_list = ['neuralnetwork', 'gradboost']
for bug in bug_list:
    if bug in models_to_be_created and use_kfold_CV:
        raise ValueError('Cannot use KFold with Neural Networks or GradBoost at this time.')

# Stratify test_train_split if no Kfold is used
if stratify_data and not use_kfold_CV:
    stratify_label = y_train
else:
    stratify_label = None

# Initialization of Lists and DFs
ensemble_predictions = []
analysis_DF = pd.DataFrame()
kfold_DF = pd.DataFrame()
total_models = 0

### K-Fold Cross Validation Inputs
# If a prevous_model is being loaded, then it automatically turns off use_kfold_CV
if use_previous_model: use_kfold_CV = False
if use_kfold_CV:
    kfold_type = (kfold_distribution, kfold_repeats)
else:
    kfold_number_of_folds = 1
    kfold_type = None

### Scaler Function Inputs
if scaler_select:
    X_train, X_test = scaleSelector(x_train, x_test, scaler_select)
else:
    X_train, X_test = x_train, x_test
Y_train, X_valid, Y_valid = y_train, None, None

# If kfold_number_of_folds == 1: Split the data using train_test_split
if kfold_number_of_folds <= 1:
    X_train, X_valid, Y_train, Y_valid = train_test_split(X_train, Y_train, test_size = split_valid_size,
                                                          random_state = 0, stratify = stratify_label)

# Random Seed
np.random.seed()

for model_selector, number_of_models in models_to_be_created.items():
    total_models += number_of_models
    print(model_selector)
    for _ in tqdm(range(0,number_of_models)):

        if model_selector == 'lightgbm':
            params, model = getModelLightGBM(use_previous_model, params, is_classifier)

        elif model_selector == 'xgboost':
            params, model = getModelXGBoost(use_previous_model, params, is_classifier)

        elif model_selector == 'neuralnetwork':
            params, model = getModelNeuralNetwork(use_previous_model, params, is_classifier)

        elif model_selector == 'lasso':
            # Lasso Model Generator
            params, model = getModelLasso(use_previous_model, params)

        elif model_selector == 'ridge':
            # Ridge Model Generator
            params, model = getModelLasso(use_previous_model, params)

        elif model_selector == 'knn':
            # KNN Model Generator
            params, model = getModelKNN(use_previous_model, params, is_classifier)

        elif model_selector == 'gradboost':
            # Gradient Boosting Generator
            params, model = getModelGradientBoosting(use_previous_model, params, is_classifier)

        elif model_selector == 'svm':
            # SVC Model Generator
            params, model = getModelSVM(use_previous_model, params, is_classifier)

        elif model_selector == 'adaboost':
            # AdaBoost with DecisionTreeClassifier Model Generator
            params, model = getModelAdaBoostTree(use_previous_model, params, is_classifier)

        elif model_selector == 'decisiontree':
            # DecisionTreeClassifier Model Generator
            params, model = getModelDecisionTree(use_previous_model, params, is_classifier)

        elif model_selector == 'randomforest':
            # RandomForest Model Generator
            params, model = getModelRandomForest(use_previous_model, params, is_classifier)


        # Model Generation based off paramList and modelList
        Pred_train, Pred_valid, Pred_test, kfold_DF = modelSelector(X_train, Y_train, X_valid, Y_valid,
                                                                    X_test, params, train_test_submission, model, is_classifier,
                                                                    kfold_number_of_folds = kfold_number_of_folds,
                                                                    kfold_type = kfold_type,
                                                                    modeltype = model_selector)

        analysis_DF = dataFrameUpdate(is_classifier, params, Y_train, Y_valid, Pred_train, Pred_valid, analysis_DF,
                                      kfold_DF, use_kfold_CV)
        if ensemble: ensemble_predictions.append(Pred_test)


if kfold_number_of_folds > 1:
    train_auc = analysis_DF['Train Auc(C)-R2(R)'].apply(lambda x: x.split('_')[0].strip()).astype('float64')
    valid_auc = analysis_DF['Valid Auc(C)-R2(R)'].apply(lambda x: x.split('_')[0].strip()).astype('float64')
else:
    train_auc = analysis_DF['Train Auc(C)-R2(R)']
    valid_auc = analysis_DF['Valid Auc(C)-R2(R)']

print(train_auc.max(), valid_auc.max())
plt.plot(range(0, total_models), train_auc, 'b', label = 'Train Auc(C)-R2(R)')
plt.plot(range(0, total_models), valid_auc, 'r', label = 'Valid Auc(C)-R2(R)')
plt.show()
if not use_previous_model:
    analysis_DF = analysis_DF.sort_values(['Valid Auc(C)-R2(R)','Train Auc(C)-R2(R)'], ascending = False)
    analysis_DF.to_csv(path + 'analysis_df.csv')

# Writes final submission file
if train_test_submission: trainFullSubmission(Pred_test, test[submission_column_names[0]],
                                              submission_column_names, ensemble, ensemble_predictions, path)

############################ Analysis of Results ##################################
analysis_DF.sort_values(['Valid Auc(C)-R2(R)','Train Auc(C)-R2(R)'], ascending = False)
