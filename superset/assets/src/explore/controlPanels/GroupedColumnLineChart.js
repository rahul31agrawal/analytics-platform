/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import { t } from '@superset-ui/translation';
import { nonEmpty, numeric } from '../validators';

export default {
  controlPanelSections: [
    {
      label: t('Query'),
      expanded: true,
      controlSetRows: [
        ['metric'],
        ['adhoc_filters'],
        ['series'],
        ['row_limit']
      ],
    },
    {
      label: t('Chart Options'),
      expanded: true,
      controlSetRows: [
        ['color_scheme', 'label_colors'],
        ['x_axis_label', 'y_axis_label'],
        ['global_opacity']
      ],
    },
  ],
  controlOverrides: {
    metric: {
      label: t('Metrics'),
      description: t('Select the numeric columns: First one will be rendered as Bar'),
      multi: true,
      validators: [nonEmpty],
    },
    global_opacity: {
      description: t('Opacity of the bars. Between 0 and 1'),
      renderTrigger: true,
    },
    series: {
      label: t('Series'),
      description: t('X-Axis for the data'),
      multi: false,
      validators: [nonEmpty]
    }
  },
};
