"""
Stacking Ensemble Model and Baseline Classifiers Definition.
Implements scikit-learn StackingClassifier with:
- Base estimators: Logistic Regression, Random Forest, Support Vector Machine (RBF kernel)
- Meta estimator: Logistic Regression with cross-validation
"""
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier

def get_base_models(random_state=42, class_weight=None):
    """
    Returns a dictionary of base classifier candidates.
    Supports optional class_weight for cost-sensitive learning.
    """
    return {
        "logistic_regression": LogisticRegression(
            max_iter=1000,
            C=1.0,
            class_weight=class_weight,
            random_state=random_state
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_split=4,
            class_weight=class_weight,
            random_state=random_state
        ),
        "svm": SVC(
            C=1.0,
            kernel="rbf",
            probability=True,
            class_weight=class_weight,
            random_state=random_state
        ),
        "decision_tree": DecisionTreeClassifier(
            max_depth=4,
            class_weight=class_weight,
            random_state=random_state
        ),
        "knn": KNeighborsClassifier(
            n_neighbors=5
        )
    }

def build_stacking_classifier(random_state=42, cv=5, class_weight=None):
    """
    Builds a StackingClassifier combining Logistic Regression, Random Forest, and SVM,
    with Logistic Regression as the final meta-learner.
    Out-of-fold cross-validation is used to train the meta-learner to prevent leakage.
    """
    base_dict = get_base_models(random_state=random_state, class_weight=class_weight)
    
    estimators = [
        ("lr", base_dict["logistic_regression"]),
        ("rf", base_dict["random_forest"]),
        ("svm", base_dict["svm"])
    ]

    final_estimator = LogisticRegression(
        C=1.0,
        max_iter=1000,
        class_weight=class_weight,
        random_state=random_state
    )

    stacking_clf = StackingClassifier(
        estimators=estimators,
        final_estimator=final_estimator,
        cv=cv,
        stack_method="predict_proba",
        passthrough=False,
        n_jobs=1
    )

    return stacking_clf
