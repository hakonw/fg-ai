<script lang="ts">
import SegmentedButton, { Segment } from '@smui/segmented-button';
import { Label } from '@smui/common';
import {Choices, type ChoiceT} from "./SelectorChoice";

export let selected: ChoiceT;
</script>

<SegmentedButton segments={Choices} let:segment singleSelect bind:selected>
    <Segment {segment}>
        <Label>{segment.name}</Label>
    </Segment>
</SegmentedButton>