from typing import Any, Optional

import pandas as pd
from visions import VisionsTypeset

from ydata_profiling.config import Settings
from ydata_profiling.model import BaseDescription, expectation_algorithms
from ydata_profiling.model.handler import Handler
from ydata_profiling.utils.dataframe import slugify
from great_expectations.checkpoint import SimpleCheckpoint


class ExpectationHandler(Handler):
    """Default handler"""

    def __init__(self, typeset: VisionsTypeset, *args, **kwargs):
        mapping = {
            "Unsupported": [expectation_algorithms.generic_expectations],
            "Text": [expectation_algorithms.categorical_expectations],
            "Categorical": [expectation_algorithms.categorical_expectations],
            "Boolean": [expectation_algorithms.categorical_expectations],
            "Numeric": [expectation_algorithms.numeric_expectations],
            "URL": [expectation_algorithms.url_expectations],
            "File": [expectation_algorithms.file_expectations],
            "Path": [expectation_algorithms.path_expectations],
            "DateTime": [expectation_algorithms.datetime_expectations],
            "Image": [expectation_algorithms.image_expectations],
        }
        super().__init__(mapping, typeset, *args, **kwargs)


class ExpectationsReportV3:
    config: Settings
    df: Optional[pd.DataFrame] = None

    @property
    def typeset(self) -> Optional[VisionsTypeset]:
        return None

    def to_expectation_suite(
        self,
        suite_name: Optional[str] = None,
        data_context: Optional[Any] = None,
        save_suite: bool = True,
        run_validation: bool = True,
        build_data_docs: bool = True,
        handler: Optional[Handler] = None,
    ) -> Any:
        """
        All parameters default to True to make it easier to access the full functionality of Great Expectations out of
        the box.
        Args:
            suite_name: The name of your expectation suite
            data_context: A user-specified data context
            save_suite: Boolean to determine whether to save the suite to .json as part of the method
            run_validation: Boolean to determine whether to run validation as part of the method
            build_data_docs: Boolean to determine whether to build data docs, save the .html file, and open data docs in
                your browser
            handler: The handler to use for building expectation

        Returns:
            An ExpectationSuite
        """
        try:
            import great_expectations as ge
        except ImportError as ex:
            raise ImportError(
                "Please install great expectations before using the expectation functionality"
            ) from ex

        # Use report title if suite is empty
        if suite_name is None:
            suite_name = slugify(self.config.title)

        # Use the default handler if none
        if handler is None:
            handler = ExpectationHandler(self.typeset)

        # Obtain the ge context and create the expectation suite
        if not data_context:
            data_context = ge.data_context.DataContext()

        data_asset = data_context.get_datasource(
            "pandas").get_asset(suite_name)

        batch_request = data_asset.build_batch_request()

        suite = data_context.add_or_update_expectation_suite(expectation_suite_name=suite_name)


        # Instantiate an in-memory pandas dataset
        validator = data_context.get_validator(batch_request=batch_request, expectation_suite=suite)

        # Obtain the profiling summary
        summary: BaseDescription = self.get_description()  # type: ignore

        # Dispatch to expectations per semantic variable type
        for name, variable_summary in summary.variables.items():
            handler.handle(variable_summary["type"], name, variable_summary, validator)

        # We don't actually update the suite object on the batch in place, so need
        # to get the populated suite from the batch
        suite = validator.get_expectation_suite(discard_failed_expectations=False)
        data_context.update_expectation_suite(suite)
        
        validation_result_identifier = None
        if run_validation:
            checkpoint_config = {
                "class_name": "SimpleCheckpoint",
                "validations": [
                    {
                        "batch_request": batch_request,
                        "expectation_suite_name": suite_name,
                    }
                ]
            }
            checkpoint = SimpleCheckpoint(
                f"_tmp_checkpoint_{suite_name}",
                data_context,
                suite,
                **checkpoint_config,

            )
            results = checkpoint.run(result_format="SUMMARY", run_name=suite_name)
            validation_result_identifier = results.list_validation_result_identifiers()[0]



        # Write expectations and open data docs
        if save_suite or build_data_docs:
            data_context.update_expectation_suite(suite)

        if build_data_docs:
            data_context.build_data_docs()
            data_context.open_data_docs(validation_result_identifier)

        return validator.get_expectation_suite()